import asyncio, json, os
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
from temporalio.client import Client as Temporal

NATS_URL = os.getenv("NATS_URL","nats://nats:4222")
SUBJECTS = ["gh.pull_request.*", "gh.release.*"]  # extend as needed
STREAM_NAME = "GH"
CONSUMER_NAME = "CODEX"

async def main():
    nc = NATS()
    await nc.connect(servers=[NATS_URL])
    js = nc.jetstream()
    t = await Temporal.connect(os.getenv("TEMPORAL_HOST","temporal:7233"),
                               namespace=os.getenv("TEMPORAL_NAMESPACE","default"))

    async def handler(msg):
        try:
            evt = json.loads(msg.data.decode())
        except Exception:
            await msg.nak()
            return
        
        # Event deduplication using delivery_id for workflow idempotency
        wf_id = f"codex-{evt.get('delivery_id') or evt.get('pull_request',{}).get('id') or hash(json.dumps(evt,sort_keys=True))}"
        
        try:
            handle = t.create_workflow_handle("CodexWorkflow", id=wf_id, task_queue="codex-task-queue")
            await handle.start(evt)
            print(f"[codex] Started workflow {wf_id} for event {evt.get('event', 'unknown')}")
            await msg.ack()
        except Exception as e:
            # Workflow already exists (idempotency) or other error
            if "already exists" in str(e).lower() or "workflow execution already started" in str(e).lower():
                print(f"[codex] Workflow {wf_id} already exists - skipping duplicate event")
                await msg.ack()  # Acknowledge duplicate to prevent redelivery
            else:
                print(f"[codex] Failed to start workflow {wf_id}: {e}")
                await msg.nak()  # Negative acknowledge for retry

    # Subscribe to durable consumer
    try:
        await js.subscribe(
            "gh.*.*",
            cb=handler,
            stream=STREAM_NAME,
            durable=CONSUMER_NAME,
            manual_ack=True
        )
        print(f"[codex] Listening on JetStream consumer {CONSUMER_NAME} for stream {STREAM_NAME}")
    except Exception as e:
        print(f"[codex] Failed to subscribe to JetStream consumer: {e}")
        print(f"[codex] Make sure to run 'make nats.setup' to create the stream and consumer")
        raise
    
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        await nc.close()

if __name__ == "__main__":
    asyncio.run(main())