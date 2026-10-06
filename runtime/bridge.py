"""One JSONL request per process. Claude Code owns authentication; Pi owns execution."""
from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import signal
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vendor' / 'transport'))
import directsdk
import directsdk_setup
from model_catalog import MODEL_METADATA, accepts_thinking_disable


def emit(value):
    print(json.dumps(value, ensure_ascii=True, allow_nan=False), flush=True)


def catalog(rows=None):
    rows = rows or [{'id': route, 'label': directsdk_setup._catalog_label(meta['canonical_model']), 'note': ''}
                    for route, meta in MODEL_METADATA.items()]
    return [{**row, 'thinkingOff': accepts_thinking_disable(row['id']),
             'contextWindow': MODEL_METADATA.get(row['id'], {}).get('context_window',
                      1_000_000 if row['id'].endswith('[1m]') else 200_000)} for row in rows]


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('status', 'catalog', 'discover'):
        operation = sys.argv[1]
        if operation == 'status':
            status = directsdk_setup.setup_status()
            emit({key: status[key] for key in ('available', 'logged_in', 'plan', 'detail')})
        else:
            emit(catalog(directsdk_setup.discover_models(timeout=20) if operation == 'discover' else None))
        return

    request = json.loads(sys.stdin.readline())
    acknowledgments = queue.Queue()
    observer_lock = threading.Lock()
    cancelled = threading.Event()

    class Client(directsdk.Client):
        def _workdir(self):
            # The Pi process created this directory atomically and owns its cleanup.
            return request['cwd']

    client = Client()  # env=None preserves the upstream fail-closed OAuth guard.

    def cancel():
        cancelled.set()
        acknowledgments.put(False)
        client.close()

    def controls():
        for line in sys.stdin:
            control = json.loads(line)
            if control.get('type') == 'ack':
                acknowledgments.put(True)
            else:
                cancel()
        cancel()  # Parent exit/closed pipe must not leave native running.

    def observe(value):
        with observer_lock:
            if cancelled.is_set():
                raise RuntimeError('Claude request cancelled')
            emit(value)
            if not acknowledgments.get(timeout=30):
                raise RuntimeError('Claude request cancelled')

    def interrupt(*_):
        threading.Thread(target=cancel, daemon=True).start()

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, interrupt)
    threading.Thread(target=controls, daemon=True).start()

    if request.get('observeStream'):
        client.on_event = lambda event: observe({'type': 'provider_event', 'event': event})
    if request.get('observeResponse'):
        original = directsdk.Admission

        class Admission(original):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.on_response = lambda status, headers: observe({
                    'type': 'response', 'status': status,
                    'headers': {key.lower(): value for key, value in headers.items()
                                if key.lower() not in ('set-cookie', 'authorization', 'proxy-authorization')},
                })

        directsdk.Admission = Admission

    try:
        with client.create(**request['payload'], stream=True) as stream:
            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                if delta.content:
                    emit({'type': 'delta', 'kind': 'text', 'delta': delta.content})
                if getattr(delta, 'reasoning_content', None):
                    emit({'type': 'delta', 'kind': 'thinking', 'delta': delta.reasoning_content})
                if hasattr(chunk, '_response'):
                    response = chunk._response.model_dump()
                    message = response['choices'][0]['message']
                    carriers = message['reasoning_details']
                    native = carriers[0]['messages'][-1]
                    emit({'type': 'result', 'text': message['content'] or '',
                          'thinking': message.get('reasoning_content') or '',
                          'toolCalls': [{'id': call['id'], 'name': call['function']['name'],
                                         'arguments': json.loads(call['function']['arguments'])}
                                        for call in message['tool_calls'] or []],
                          'replay': carriers,
                          'refusal': message.get('refusal'),
                          'finish': response['choices'][0]['finish_reason'],
                          'rawStopReason': native.get('stop_reason'),
                          'responseId': native.get('id'), 'responseModel': native.get('model'),
                          'usage': response['usage']})
    except Exception as error:
        emit({'type': 'error', 'message': str(error), 'status': getattr(error, 'status_code', None)})
        sys.exit(1)
    finally:
        client.close()


if __name__ == '__main__':
    main()
