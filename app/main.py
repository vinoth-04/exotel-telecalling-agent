
import os
import sqlite3
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketState
from starlette.websockets import WebSocketDisconnect
from prompts.clinic_system_prompt import SYSTEM_PROMPT

# Pipecat imports for full-duplex voice orchestration
from pipecat.runner.utils import parse_telephony_websocket
from pipecat.serializers.exotel import ExotelFrameSerializer
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.transports.base_transport import BaseTransport
# from pipecat.transports.websocket.fastapi import (
    # FastAPIWebsocketParams,
    # FastAPIWebsocketTransport,
# )
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from database.tools import *

load_dotenv()

app = FastAPI()

# =========================================================
# 🗄️ DATABASE LAYER (SQLite)
# =========================================================
DB_NAME = "clinic.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time TEXT,
            phone TEXT,
            reason TEXT,
            urgency TEXT,
            status TEXT DEFAULT 'confirmed'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

SYSTEM_PROMPT = SYSTEM_PROMPT

# =========================================================
# 📞 EXOTEL WEBSOCKET PIPELINE
# =========================================================
@app.websocket("/ws")
async def exotel_ws(websocket: WebSocket):
    await websocket.accept()
    print("Telephony session started...")

    try:
        # 1. Parse Exotel Initial Handshake
        transport_type, call_data = await parse_telephony_websocket(websocket)
        
        # 2. Setup Telephony Serializer
        serializer = ExotelFrameSerializer(
            stream_sid=call_data["stream_id"],
            call_sid=call_data["call_id"],
        )

        # 3. Setup Transport & VAD (Voice Activity Detection)
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
                serializer=serializer,
            ),
        )

        transport.loop = asyncio.get_event_loop()
        # 4. Initialize AI Services
        stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
        tts = ElevenLabsTTSService(api_key=os.getenv("ELEVENLABS_API_KEY"),voice_id="JBFqnCBsd6RMkjVDRZzb",model="eleven_turbo_v2_5",)

        # 5. Register Scenario Tools
        llm.register_function("check_availability", check_availability)
        llm.register_function("book_appointment", book_appointment)
        llm.register_function("cancel_appointment", cancel_appointment)
        llm.register_function("reschedule_appointment", reschedule_appointment)
        llm.register_function("check_insurance", check_insurance)
        llm.register_function("log_doctor_message", log_doctor_message)
        llm.register_function("request_human_handoff", request_human_handoff)

        # 6. Build the Pipeline
        context = LLMContext([{"role": "system", "content": SYSTEM_PROMPT}])
        context_agg = LLMContextAggregatorPair(context)

        pipeline = Pipeline([
            transport.input(),    # Receive audio from Exotel
            stt,                  # Audio -> Text
            context_agg.user(),   # Accumulate user turn
            llm,                  # Process logic / call tools
            tts,                  # Text -> Audio
            transport.output(),   # Send audio to Exotel
            context_agg.assistant(),
        ])

        # 7. Execute Task
        task = PipelineTask(pipeline, params=PipelineParams(
            audio_in_sample_rate=8000,   # Telephony standard
            audio_out_sample_rate=8000,
            allow_interruptions=True,
        ))        
        try:
            await task.run(transport)
        except WebSocketDisconnect:
            print("📴 WebSocket disconnected by Exotel")
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
        finally:
            await task.cancel()


    except Exception as e:
        print(f"❌ Connection Error: {e}")
    finally:
        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
