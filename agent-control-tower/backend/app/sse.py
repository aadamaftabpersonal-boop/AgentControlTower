"""Server-Sent Events stream for live agent/checkpoint updates (API-03, LIVE-01/02).

SSE, not WebSockets — the technical spec locks this as the architecture
decision (simpler to debug under the hackathon timeline). Implementation is
poll-and-diff on top of the existing synchronous `ingest_checkpoints()`
rather than a push-based watcher: the CLI has no watch mode, so polling is
the only source of truth available, and diffing against the previous
snapshot is what turns "poll the same normalizer every N seconds" into an
event stream instead of a firehose of duplicates.
"""

import asyncio
import json

from fastapi.responses import StreamingResponse

from app import normalizer, registry

POLL_INTERVAL_SECONDS = 2.0


async def _event_generator():
    seen_checkpoint_ids: set[str] = set()
    # Emit an initial full snapshot immediately so a freshly connected client
    # doesn't wait a full poll interval to see current state.
    first = True
    while True:
        try:
            # ingest_checkpoints() shells out synchronously; running it inline
            # in this async generator would block the whole event loop for
            # every other connection (including /api/checkpoints and
            # /api/agents) each poll tick. to_thread keeps the loop free.
            result = await asyncio.to_thread(normalizer.ingest_checkpoints)
            reg = registry.build_agent_registry(result)
            new_ids = {cp.checkpoint_id for cp in result.checkpoints if cp.checkpoint_id}

            if first:
                yield f"event: snapshot\ndata: {reg.model_dump_json()}\n\n"
                seen_checkpoint_ids = new_ids
                first = False
            else:
                added = new_ids - seen_checkpoint_ids
                if added:
                    seen_checkpoint_ids = new_ids
                    yield f"event: update\ndata: {reg.model_dump_json()}\n\n"
        except Exception as exc:  # noqa: BLE001 — degrade the stream, never kill it (LIVE-02)
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def stream_agent_events() -> StreamingResponse:
    return StreamingResponse(_event_generator(), media_type="text/event-stream")
