import os
import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Configuration depuis variables d'environnement (jamais en dur)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "changeme")
API_PORT = int(os.getenv("API_PORT", "8000"))

app = FastAPI(title="Task Manager API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

pool: Optional[asyncpg.Pool] = None


class Task(BaseModel):
    title: str
    description: str = ""
    duration: int = 0


@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD, min_size=1, max_size=5
    )
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT DEFAULT '',
                duration INTEGER DEFAULT 0,
                done BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)


@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()


@app.get("/health")
async def health():
    """Toujours 200 : le processus répond."""
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    """200 uniquement si la base répond."""
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"db not ready: {e}")


# --- CRUD Tâches ---

@app.post("/tasks", status_code=201)
async def create_task(task: Task):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO tasks (title, description, duration) VALUES ($1, $2, $3) RETURNING *",
            task.title, task.description, task.duration
        )
    return dict(row)


@app.get("/tasks")
async def list_tasks():
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tasks ORDER BY id DESC")
    return [dict(r) for r in rows]


@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row)


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE tasks SET title=$1, description=$2, duration=$3 WHERE id=$4 RETURNING *",
            task.title, task.description, task.duration, task_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row)


@app.patch("/tasks/{task_id}/done")
async def toggle_done(task_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE tasks SET done = NOT done WHERE id=$1 RETURNING *", task_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row)


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM tasks WHERE id = $1", task_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Task not found")