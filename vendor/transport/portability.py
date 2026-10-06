"""Selected MIT Hermes core helpers, used only by the vendored transport."""

from __future__ import annotations

from typing import Any, Callable, Optional, Sequence

_UNION_KEYS = ("anyOf", "oneOf")

_UNION_META_KEYS = ("title", "description", "default", "examples")  # copied onto replacements

def _rewrite(schema: Any, fn: Callable[[dict], Any]) -> Any:
    """Bottom-up map over a schema tree: lists/dicts recurse, then *fn* sees each dict."""
    if isinstance(schema, list):
        return [_rewrite(item, fn) for item in schema]
    if not isinstance(schema, dict):
        return schema
    return fn({k: _rewrite(v, fn) for k, v in schema.items()})

def _is_null_branch(item: Any) -> bool:
    return isinstance(item, dict) and item.get("type") == "null"

def _carry_union_meta(outer: dict, replacement: dict, *, skip_default_on_ref: bool) -> None:
    """Copy outer-union metadata onto *replacement* where absent (``default`` is illegal beside
    ``$ref`` on strict backends, hence ``skip_default_on_ref``)."""
    for meta_key in _UNION_META_KEYS:
        if meta_key in outer and meta_key not in replacement and not (
                skip_default_on_ref and meta_key == "default" and "$ref" in replacement):
            replacement[meta_key] = outer[meta_key]

def strip_nullable_unions(schema: Any, *, keep_nullable_hint: bool = True) -> Any:
    """Collapse ``anyOf``/``oneOf`` nullable unions (MCP/Pydantic optional fields) to the single
    non-null branch: Anthropic rejects the null branch and optionality already lives in the parent's
    ``required``. Only when a null branch was dropped AND exactly one non-null branch survives.
    ``keep_nullable_hint`` sets ``nullable: true`` for runtime ``"null"`` → ``None`` coercion."""
    def collapse(stripped: dict) -> Any:
        for key in _UNION_KEYS:
            variants = stripped.get(key)
            if not isinstance(variants, list):
                continue
            non_null = [item for item in variants if not _is_null_branch(item)]
            if len(non_null) == 1 and len(non_null) != len(variants):
                replacement = dict(non_null[0]) if isinstance(non_null[0], dict) else {}
                if keep_nullable_hint:
                    replacement.setdefault("nullable", True)
                _carry_union_meta(stripped, replacement, skip_default_on_ref=True)
                return _rewrite(replacement, collapse)  # the survivor may itself be a union
        return stripped
    return _rewrite(schema, collapse)

EFFORT_LADDER: tuple[str, ...] = ("none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra")

def clamp_effort(
    effort: Optional[str], supported: Optional[Sequence[str]], overrides: Optional[dict[str, str]] = None,
) -> Optional[str]:
    """Clamp a requested reasoning effort onto a wire's supported levels.

    ``overrides`` (a declared vendor mapping, e.g. Kimi K3 ``medium → high``) is consulted
    first. Otherwise the request passes through unchanged when it is supported, when the
    supported set is unknown/empty, or when it isn't a recognized ladder level (custom
    providers may use bespoke names). Else the **nearest weaker** supported level is returned
    so a clamp never escalates cost; when nothing weaker exists, the weakest supported level
    (the provider's floor is the closest honest match). Monotonic: a stronger request never
    resolves weaker than a weaker request would.
    """
    requested = str(effort or "").strip().lower()
    if not requested or not supported:
        return effort
    supported_norm = [lvl for lvl in (str(s).strip().lower() for s in supported) if lvl in EFFORT_LADDER]
    if not supported_norm or requested in supported_norm:
        return effort
    if overrides and overrides.get(requested) in supported_norm:
        return overrides[requested]
    if requested not in EFFORT_LADDER:
        return effort
    # "none" disables reasoning — never a degradation target for an enabled ask
    # (clamping "minimal" to "none" would silently switch thinking off).
    candidates = [level for level in supported_norm if level != "none"]
    if not candidates:
        return effort
    requested_idx = EFFORT_LADDER.index(requested)
    below = [level for level in candidates if EFFORT_LADDER.index(level) < requested_idx]
    return max(below, key=EFFORT_LADDER.index) if below else min(candidates, key=EFFORT_LADDER.index)
