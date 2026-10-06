"""Exercise Pi and Claude Code: loopback fixtures by default, real subscription inference with --live."""
from __future__ import annotations

import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import queue
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = shutil.which('claude')
PI = shutil.which('pi')


def extension_entry():
    return ROOT / json.loads((ROOT / 'package.json').read_text())['pi']['extensions'][0]


def source_identity():
    paths = [ROOT / 'package.json', ROOT / 'pnpm-lock.yaml', ROOT / 'acceptance' / 'provider.py', ROOT / 'vendor' / 'source.json',
             *sorted((ROOT / 'src').glob('*.ts')), *sorted((ROOT / 'scripts').glob('*.mjs')),
             *sorted((ROOT / 'dist').glob('*.js')), *sorted((ROOT / 'runtime').glob('*.py')), *sorted((ROOT / 'vendor' / 'transport').glob('*.py'))]
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def sse(blocks, stop, refusal=None):
    usage = {'input_tokens': 0, 'output_tokens': 10, 'cache_read_input_tokens': 12, 'cache_creation_input_tokens': 20,
             'cache_creation': {'ephemeral_1h_input_tokens': 20, 'ephemeral_5m_input_tokens': 0}}
    events = [{'type': 'message_start', 'message': {'id': 'msg_fixture', 'type': 'message', 'role': 'assistant',
               'model': 'claude-sonnet-5-5', 'content': [], 'usage': usage}}]
    for index, block in enumerate(blocks):
        events.append({'type': 'content_block_start', 'index': index, 'content_block': block})
        events.append({'type': 'content_block_stop', 'index': index})
    events += [{'type': 'message_delta', 'delta': {'stop_reason': stop, 'stop_sequence': None,
               **({'stop_details': {'explanation': refusal, 'category': 'fixture'}} if refusal else {})}, 'usage': usage},
               {'type': 'message_stop'}]
    return ''.join('data: ' + json.dumps(event) + '\n\n' for event in events).encode()


def exercise_live(run, receipt, check):
    if os.name != 'posix':
        raise RuntimeError('Live process-reaping verification currently requires POSIX ps.')
    agent = run / 'agent'
    agent.mkdir()
    (agent / 'settings.json').write_text(json.dumps({'retry': {'enabled': False}, 'compaction': {'enabled': False},
                                                    'defaultThinkingLevel': 'xhigh'}))
    env = {**os.environ, 'PI_CODING_AGENT_DIR': str(agent), 'PI_CLAUDE_CODE_PYTHON': sys.executable,
           'PI_CLAUDE_CODE_COMMAND': CLAUDE, 'PI_CLAUDE_CODE_TELEMETRY': 'false'}
    # Native HOME/config remain inherited. No fixture wrapper, auth override, or credential copies.
    hook_log = run / 'hooks.jsonl'
    hooks = run / 'hooks.ts'
    hooks.write_text('''import { appendFileSync } from "node:fs";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
export default function (pi: ExtensionAPI) {
  const log = (value: object) => appendFileSync(''' + json.dumps(str(hook_log)) + ''', JSON.stringify(value) + "\\n");
  pi.on("before_provider_request", () => { log({type: "before_provider_request"}); });
  pi.on("after_provider_response", (event) => { log({type: event.type, status: event.status}); });
  pi.on("provider_stream_event", (event) => { log({type: event.type, provider: event.provider, model: event.model}); });
}
''')
    # A deterministic bitmap, with no answer encoded in the prompt or filename.
    pixels = bytearray()
    for y in range(200):
        pixels.append(0)
        for x in range(360):
            blue = any((x - center) ** 2 + (y - 100) ** 2 <= 35 ** 2 for center in (60, 180, 300))
            pixels.extend((0, 75, 245) if blue else (255, 255, 255))
    def png_chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    image = (b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', struct.pack('>IIBBBBB', 360, 200, 8, 2, 0, 0, 0))
             + png_chunk(b'IDAT', zlib.compress(pixels)) + png_chunk(b'IEND', b''))
    target, cancelled_target = run / 'result.txt', run / 'cancelled.txt'
    command = [PI, '--offline', '--no-extensions', '--no-skills', '--no-mcp', '--no-context-files',
               '--no-prompt-templates', '--no-session', '-e', str(extension_entry()), '-e', str(hooks),
               '--model', 'claude-code/claude-sonnet-5-5[1m]', '--mode', 'rpc', '--tools', 'write',
               '--system-prompt', 'Follow the requested output format. Only the declared Pi write tool may modify files.']
    incoming = queue.Queue()
    captured = []
    stderr = run / 'stderr.txt'
    with stderr.open('wb') as error_output:
        process = subprocess.Popen(command, env=env, cwd=run, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=error_output)
        def reader():
            try:
                for line in process.stdout:
                    incoming.put(json.loads(line))
            finally:
                incoming.put(None)
        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        events = []
        def send(value):
            process.stdin.write(json.dumps(value).encode() + b'\n')
            process.stdin.flush()
        def until(predicate, seconds=180):
            deadline = time.monotonic() + seconds
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Pi RPC did not reach the requested acceptance state.')
                row = incoming.get(timeout=remaining)
                if row is None:
                    raise RuntimeError('Pi RPC exited before reaching the requested acceptance state.')
                events.append(row)
                if row.get('type') == 'response' and row.get('success') is False:
                    raise RuntimeError(row.get('error', 'RPC command failed'))
                if predicate(row):
                    return row
        def descendants():
            rows = []
            for line in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,pgid=,comm='], text=True).splitlines():
                pid, parent, group, executable = line.strip().split(None, 3)
                rows.append({'pid': int(pid), 'parentPid': int(parent), 'groupPid': int(group), 'executable': executable})
            owned = {process.pid}
            while True:
                expanded = owned | {row['pid'] for row in rows if row['parentPid'] in owned}
                if expanded == owned:
                    break
                owned = expanded
            return [row for row in rows if row['pid'] in owned and row['pid'] != process.pid]
        def exited(pid):
            try:
                os.kill(pid, 0)
                return False
            except ProcessLookupError:
                return True
        receipt['runs'] = {}
        try:
            send({'id': 'main', 'type': 'prompt', 'message':
                  f"Describe the attachment as '<count in words> <color> <shape plural>'. Use write to save only those words "
                  f"to {target}. Then reply with exactly PI_CLAUDE_CODE_LIVE_OK. Do not use any other tools.",
                  'images': [{'type': 'image', 'data': base64.b64encode(image).decode(), 'mimeType': 'image/png'}]})
            until(lambda row: row.get('type') == 'agent_settled')
            receipt['runs']['main'] = {'events': list(events), 'effect': target.read_text() if target.exists() else None,
                                        'attachmentSha256': hashlib.sha256(image).hexdigest()}
            check(target.exists() and target.read_text().strip().rstrip('.').lower() == 'three blue circles',
                  'Real subscription image inference drives the correct durable Pi tool effect')
            tools = [row for row in events if row.get('type') == 'tool_execution_end']
            check(len(tools) == 1 and tools[0]['toolName'] == 'write' and not tools[0]['isError'],
                  'Exactly one Pi-owned write completes on the real subscription path')
            assistants = [row['message'] for row in events if row.get('type') == 'message_end'
                          and row['message']['role'] == 'assistant']
            check(assistants[-1]['stopReason'] == 'stop' and ''.join(block.get('text', '') for block
                  in assistants[-1]['content']).strip() == 'PI_CLAUDE_CODE_LIVE_OK',
                  'Real tool-result replay completes with the requested final text')
            observed_hooks = [json.loads(line) for line in hook_log.read_text().splitlines()]
            check(observed_hooks[0]['type'] == 'before_provider_request'
                  and sum(row['type'] == 'after_provider_response' and row['status'] == 200 for row in observed_hooks) == 2
                  and any(row['type'] == 'provider_stream_event' and row['provider'] == 'claude-code' for row in observed_hooks),
                  'Real request, response and native-stream hooks reach Pi')
            receipt['runs']['main']['hooks'] = observed_hooks
            events.clear()
            send({'id': 'cancel', 'type': 'prompt', 'message':
                  f'Print 20000 numbered lines, one per number. Only after finishing every line, write FINISHED to {cancelled_target}.'})
            until(lambda row: row.get('type') == 'message_update'
                  and row.get('assistantMessageEvent', {}).get('type') in ('text_delta', 'thinking_delta'))
            captured = descendants()
            receipt['runs']['cancel'] = {'ownedProcessesBeforeAbort': captured}
            check(any('python' in row['executable'].lower() for row in captured)
                  and any(row['pid'] == row['groupPid'] for row in captured),
                  'Cancellation begins after observing streaming with owned bridge and native processes')
            started = time.monotonic()
            send({'id': 'abort', 'type': 'abort'})
            until(lambda row: row.get('type') == 'response' and row.get('id') == 'abort', seconds=20)
            elapsed = time.monotonic() - started
            receipt['runs']['cancel'].update(events=list(events), abortAckSeconds=elapsed)
            aborted = next((row['message'] for row in events if row.get('type') == 'message_end'
                            and row['message'].get('stopReason') == 'aborted'), None)
            check(aborted is not None and aborted['diagnostics'][0]['details']['status'] == 'unknown'
                  and aborted['diagnostics'][0]['details']['source'] == 'unavailable',
                  'Interrupted generation labels incomplete accounting as unknown, not free')
            check(aborted is not None and not cancelled_target.exists()
                  and not any(row.get('type', '').startswith('tool_execution_') for row in events),
                  'Live cancellation is terminal and publishes no tool effects')
            deadline = time.monotonic() + 5
            while any(not exited(row['pid']) for row in captured) and time.monotonic() < deadline:
                time.sleep(0.05)
            exit_elapsed = time.monotonic() - started
            receipt['runs']['cancel']['processExitSeconds'] = exit_elapsed
            check(all(exited(row['pid']) for row in captured) and exit_elapsed < 10,
                  'Owned native and bridge processes exit before the hard-kill fallback')
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
            thread.join(timeout=2)
            receipt['stderr'] = stderr.read_text()[-2000:]
            receipt['cleanup'] = {'piExit': process.returncode,
                                  'remainingCapturedPids': [row['pid'] for row in captured if not exited(row['pid'])]}
        check(process.returncode == 0 and not receipt['cleanup']['remainingCapturedPids'],
              'Pi shuts down cleanly without captured descendants')


def main(live=False):
    if not PI or not CLAUDE:
        raise SystemExit('Acceptance requires pi and the official claude executable on PATH.')
    artifacts = ROOT / '.artifacts'
    artifacts.mkdir(exist_ok=True)
    receipt = {'candidateSha256': source_identity(), 'replay': 'pnpm acceptance:live' if live else 'pnpm acceptance',
               'pi': subprocess.check_output([PI, '--version'], text=True).strip(),
               'claude': subprocess.check_output([CLAUDE, '--version'], text=True).strip(),
               'python': sys.version.split()[0], 'platform': sys.platform,
               'fixture': 'real subscription; native sign-in; isolated Pi state' if live
                          else 'owned loopback SSE peer; synthetic auth; no Anthropic requests',
               'assertions': [], 'status': 'failed'}
    output = artifacts / f'acceptance-{"live-" if live else ""}{time.time_ns()}.json'

    def check(condition, name):
        receipt['assertions'].append({'name': name, 'passed': bool(condition)})
        assert condition, name

    try:
        with tempfile.TemporaryDirectory(prefix='pi-provider-acceptance-') as tmp:
            run = Path(tmp)
            if live:
                exercise_live(run, receipt, check)
                receipt['status'] = 'passed'
                return
            calls = []
            target = run / 'main-effect.txt'
            rejected = run / 'refused-effect.txt'
            effect = 'ACCEPTANCE_DATA_\u2028_✓'
            refusal = 'The fixture declined this request.'

            class Peer(BaseHTTPRequestHandler):
                def log_message(self, *_):
                    pass

                def do_POST(self):
                    body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    # Never retain request headers, even though fixture auth is synthetic.
                    calls.append(body)
                    mode = self.server.mode
                    if mode == 'main' and len(calls) == 1:
                        assert not target.exists(), 'Native executed a tool before Pi received the call'
                        blocks = [{'type': 'tool_use', 'id': 'toolu_fixture', 'name': 'mcp__pi__write',
                                   'input': {'path': str(target), 'content': effect}}]
                        stop = 'tool_use'
                    elif mode == 'refusal':
                        blocks = [{'type': 'tool_use', 'id': 'toolu_refused', 'name': 'mcp__pi__write',
                                   'input': {'path': str(rejected), 'content': 'must not exist'}}]
                        stop = 'refusal'
                    else:
                        blocks = [{'type': 'text', 'text': 'ACCEPTANCE_OK' if len(calls) == 2 else 'ACCEPTANCE_RESUME_OK'}]
                        stop = 'end_turn'
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('request-id', 'acceptance-request')
                    self.end_headers()
                    self.wfile.write(sse(blocks, stop, refusal if mode == 'refusal' else None))

            peer = ThreadingHTTPServer(('127.0.0.1', 0), Peer)
            peer.mode = 'main'
            thread = threading.Thread(target=peer.serve_forever, daemon=True)
            thread.start()
            try:
                # Explicit fixture boundary: retarget the transport's HTTPS upstream in this child only.
                # Production has no upstream override and still constructs Client(env=None).
                wrapper = run / 'fixture-python'
                wrapper.write_text(f'''#!{sys.executable}
import json, os, runpy, sys
from pathlib import Path
sys.path.insert(0, {str(ROOT / 'vendor' / 'transport')!r})
import directsdk, directsdk_setup
Original = directsdk.Admission
class Admission(Original):
    def __init__(self, upstream, *args, **kwargs):
        super().__init__({f'http://127.0.0.1:{peer.server_port}'!r}, *args, **kwargs)
directsdk.Admission = Admission
original_obj = directsdk.obj
def obj(value):
    # The bridge reads the final response, which is constructed before its stream chunk.
    if isinstance(value, dict) and value.get('object') == 'chat.completion':
        Path({str(run / 'accounting.json')!r}).write_text(json.dumps(value['usage']['native_cost']))
        if Path({str(run / 'malformed-cost')!r}).exists():
            injected = {{'total_cost_usd': 0, 'modelUsage': {{'invalid': None}}}}
            Path({str(run / 'injected-cost.json')!r}).write_text(json.dumps(injected))
            value = {{**value, 'usage': {{**value['usage'], 'native_cost': injected}}}}
    return original_obj(value)
directsdk.obj = obj
directsdk_setup.setup_status = lambda **kwargs: {{'available': True, 'logged_in': True, 'plan': 'fixture', 'detail': ''}}
# Fake native authentication is confined to this fixture process, never copied from the user.
os.environ['CLAUDE_CODE_OAUTH_TOKEN'] = 'fixture-not-a-production-credential'
os.environ['CLAUDE_CONFIG_DIR'] = {str(run / 'claude-config')!r}
for key in ('CLAUDE_SUBSCRIPTION_DIRECTSDK_CONFIG_DIR', 'PI_CLAUDE_CODE_CONFIG_DIR'):
    os.environ.pop(key, None)
sys.argv = sys.argv[3:]
runpy.run_path(sys.argv[0], run_name='__main__')
''')
                wrapper.chmod(0o700)
                (run / 'claude-config').mkdir()
                (run / 'agent').mkdir()
                (run / 'agent' / 'settings.json').write_text(json.dumps({'retry': {'enabled': False},
                    'compaction': {'enabled': False}, 'defaultThinkingLevel': 'xhigh'}))
                env = dict(os.environ)
                for key in ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL', 'ANTHROPIC_FOUNDRY_API_KEY',
                            'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY'):
                    env.pop(key, None)
                env.update(PI_CODING_AGENT_DIR=str(run / 'agent'), PI_CLAUDE_CODE_PYTHON=str(wrapper),
                           PI_CLAUDE_CODE_COMMAND=CLAUDE, HOME=str(run), PI_CLAUDE_CODE_TELEMETRY='false')
                base = [PI, '--offline', '--no-extensions', '--no-skills', '--no-mcp', '--no-context-files',
                        '--no-prompt-templates', '-e', str(extension_entry()),
                        '--model', 'claude-code/claude-sonnet-5-5[1m]', '--mode', 'json', '--tools', 'write',
                        '--system-prompt', 'Use the declared tool when required.']

                def invoke(arguments, label):
                    result = subprocess.run(base + arguments, env=env, cwd=run, stdin=subprocess.DEVNULL,
                                            capture_output=True, text=True, timeout=90)
                    events = [json.loads(line) for line in result.stdout.split('\n') if line.strip()]
                    accounting = run / 'accounting.json'
                    receipt.setdefault('runs', {})[label] = {'exit': result.returncode, 'events': events,
                        'nativeCost': json.loads(accounting.read_text()) if accounting.exists() else None,
                        'fixtureInjectedCost': json.loads((run / 'injected-cost.json').read_text())
                            if (run / 'injected-cost.json').exists() else None,
                        'stderr': result.stderr[-2000:]}
                    assert result.returncode == 0, result.stderr
                    errors = [row['message'].get('errorMessage') for row in events if row.get('type') == 'message_end'
                              and row['message'].get('stopReason') in ('error', 'aborted')]
                    assert not errors, errors
                    return events

                session = run / 'session.jsonl'
                events = invoke(['--session', str(session), 'Write the requested fixture data.'], 'main')
                check(target.read_text() == effect, 'Pi completed the durable tool effect')
                executions = [row for row in events if row.get('type') == 'tool_execution_end']
                check(len(executions) == 1 and executions[0]['toolName'] == 'write' and not executions[0]['isError'],
                      'Exactly one Pi-owned tool execution')
                check(len(calls) == 2, 'Exactly one upstream request per each of two Pi model calls')
                assistants = [row['message'] for row in events if row.get('type') == 'message_end'
                              and row['message']['role'] == 'assistant']
                check(assistants[-1]['content'][0]['text'] == 'ACCEPTANCE_OK', 'Tool follow-up reaches the user')
                check(assistants[-1]['usage']['input'] == 0 and assistants[-1]['usage']['cacheRead'] == 12
                      and assistants[-1]['usage']['cacheWrite'] == 20
                      and assistants[-1]['usage']['cacheWrite1h'] == 20, 'Native usage preserves zero and cache TTL buckets')
                replayed = [block for message in calls[1]['messages'] for block in message.get('content', [])
                            if isinstance(block, dict) and block.get('type') == 'tool_result']
                check(len(replayed) == 1 and replayed[0]['tool_use_id'] == 'toolu_fixture'
                      and 'Successfully wrote' in json.dumps(replayed[0]['content']), 'Canonical Pi tool result is replayed')
                events = invoke(['--session', str(session), 'Confirm the previous result.'], 'resume')
                check(len(calls) == 3, 'Session restart adds exactly one upstream request')
                check(any(block.get('type') == 'tool_use' for message in calls[2]['messages']
                          for block in message.get('content', []) if isinstance(block, dict)), 'Native carrier survives Pi session restart')
                check(any(row.get('type') == 'message_end' and row['message'].get('role') == 'assistant'
                          and any(block.get('text') == 'ACCEPTANCE_RESUME_OK' for block in row['message']['content'])
                          for row in events), 'Resumed response reaches the user')

                calls.clear()
                peer.mode = 'refusal'
                events = invoke(['--no-session', 'Perform the requested write.'], 'refusal')
                check(len(calls) == 1, 'Refused request cannot trigger an extra upstream generation')
                check(not rejected.exists(), 'Refused tool has no durable effect')
                check(not any(row.get('type', '').startswith('tool_execution_') for row in events),
                      'No Pi tool executes from a refused response')
                check(any(row.get('type') == 'message_end' and row['message'].get('rawStopReason') == 'refusal'
                          and row['message']['stopReason'] == 'stop'
                          and any(block.get('text') == refusal for block in row['message']['content']) for row in events),
                      'Refusal explanation is terminal and visible')
                calls.clear()
                peer.mode = 'accounting'
                (run / 'malformed-cost').touch()
                events = invoke(['--no-session', 'Reply with the fixture response.'], 'accounting')
                assistant = next(row['message'] for row in events if row.get('type') == 'message_end'
                                 and row['message']['role'] == 'assistant')
                check(assistant['stopReason'] == 'stop', 'Malformed optional cost does not discard completed content')
                check(assistant['diagnostics'][0]['details']['source'] == 'catalog-list-estimate'
                      and assistant['usage']['cost']['total'] > 0, 'Malformed cost falls back to known catalog pricing')
                check(abs(assistant['usage']['cost']['cacheWrite'] - 0.00008) < 1e-12,
                      'Catalog fallback uses the reported one-hour cache-write rate')
                receipt['status'] = 'passed'
                receipt['upstreamRequests'] = {'mainAndResume': 3, 'refusal': 1, 'accounting': len(calls)}
            finally:
                peer.shutdown()
                peer.server_close()
                thread.join()
    except Exception as error:
        receipt['error'] = str(error)
        raise
    finally:
        output.write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + '\n')
        print(f'Acceptance {receipt["status"]}: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Use real subscription inference, including a cancelled request.')
    main(live=parser.parse_args().live)
