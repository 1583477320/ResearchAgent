"""Phase 1 verification: Memory system initialization and LLM cache."""

import sys
from pathlib import Path

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).parent))

from src.memory import MemorySystem
from src.memory.database import Database
from src.memory.services.cache_service import CacheService
from src.utils.config import settings


def test_database_init():
    """Test database creation and schema initialization."""
    print("=== Test 1: Database initialization ===")
    db_path = "test_memory_verify.db"
    db = Database(db_path)
    db.init_schema()

    # Verify tables exist
    tables = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [row["name"] for row in tables]
    print(f"  Tables created: {table_names}")

    expected = [
        "research_sessions",
        "working_memory_entries",
        "paper_analyses",
        "paper_analyses_fts",
        "llm_cache",
        "user_preferences",
    ]
    for table in expected:
        assert table in table_names, f"Table {table} not found!"
        print(f"  ✓ {table}")

    db.close()
    # Clean up
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_models():
    """Test Pydantic model instantiation."""
    print("=== Test 2: Pydantic models ===")
    from src.memory.models import (
        ResearchSession,
        MemoryEntry,
        PaperAnalysisRecord,
        LLMCacheEntry,
        UserPreference,
    )

    session = ResearchSession(topic="test topic", status="running")
    assert session.id, "Session should have auto-generated id"
    print(f"  ✓ ResearchSession: id={session.id}, topic={session.topic}")

    entry = MemoryEntry(
        session_id=session.id,
        node_name="plan",
        agent_name="planner",
        step_number=1,
    )
    assert entry.id and entry.created_at
    print(f"  ✓ MemoryEntry: id={entry.id}")

    analysis = PaperAnalysisRecord(
        session_id=session.id,
        paper_title="Test Paper",
        problem="A test problem",
        method="A test method",
    )
    assert analysis.id
    print(f"  ✓ PaperAnalysisRecord: id={analysis.id}")

    cache_entry = LLMCacheEntry(
        model_name="deepseek-chat",
        prompt_hash="abc123",
        response_text="test response",
    )
    assert cache_entry.id
    print(f"  ✓ LLMCacheEntry: id={cache_entry.id}")

    pref = UserPreference(key="max_papers", value="10")
    print(f"  ✓ UserPreference: {pref.key}={pref.value}")
    print("  PASSED\n")


def test_cache_repo():
    """Test cache repository CRUD."""
    print("=== Test 3: Cache repository ===")
    db_path = "test_memory_verify.db"
    db = Database(db_path)
    db.init_schema()

    from src.memory.repositories.cache_repo import CacheRepo

    repo = CacheRepo(db)

    # Insert
    entry_id = repo.save(
        model_name="deepseek-chat",
        prompt_hash="test_hash_123",
        system_prompt="You are a helpful assistant.",
        user_prompt="Hello",
        response_text="Hi there!",
    )
    print(f"  ✓ Insert: id={entry_id}")

    # Query
    row = repo.get_by_hash("deepseek-chat", "test_hash_123")
    assert row is not None, "Cache entry should be found"
    assert row["response_text"] == "Hi there!"
    print(f"  ✓ Query: response_text='{row['response_text']}'")

    # Get response shortcut
    response = repo.get_response("deepseek-chat", "test_hash_123")
    assert response == "Hi there!"
    print(f"  ✓ get_response: '{response}'")

    # Duplicate insert should update hit count
    repo.save(
        model_name="deepseek-chat",
        prompt_hash="test_hash_123",
        system_prompt="You are a helpful assistant.",
        user_prompt="Hello",
        response_text="Hi there!",
    )
    row = repo.get_by_hash("deepseek-chat", "test_hash_123")
    # hit_count is incremented by get_by_hash too, so it could be 3
    assert row["hit_count"] >= 2
    print(f"  ✓ Duplicate update: hit_count={row['hit_count']}")

    # Stats
    stats = repo.stats()
    print(f"  ✓ Stats: total_entries={stats['total_entries']}, total_hits={stats['total_hits']}")

    # List recent
    recent = repo.list_recent(limit=5)
    print(f"  ✓ List recent: {len(recent)} entries")

    db.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_cache_service():
    """Test cache service with prompt hashing."""
    print("=== Test 4: Cache service ===")
    db_path = "test_memory_verify.db"
    db = Database(db_path)
    db.init_schema()

    from src.memory.repositories.cache_repo import CacheRepo
    from src.memory.services.cache_service import CacheService

    repo = CacheRepo(db)
    svc = CacheService(repo, enabled=True)

    # Hash should be deterministic
    h1 = svc.hash_prompt("system", "user")
    h2 = svc.hash_prompt("system", "user")
    assert h1 == h2, "Same input should produce same hash"
    print(f"  ✓ Deterministic hash: {h1[:16]}...")

    # Different prompts = different hashes
    h3 = svc.hash_prompt("system2", "user")
    assert h1 != h3, "Different input should produce different hash"
    print(f"  ✓ Different hashes for different inputs")

    # Set and get
    svc.set("deepseek-chat", "sys prompt", "user prompt", "cached output")
    result = svc.get("deepseek-chat", "sys prompt", "user prompt")
    assert result == "cached output"
    print(f"  ✓ Cache set/get: '{result}'")

    # Miss
    miss = svc.get("deepseek-chat", "unknown", "prompt")
    assert miss is None
    print(f"  ✓ Cache miss returns None")

    # Disabled cache
    svc.enabled = False
    miss2 = svc.get("deepseek-chat", "sys prompt", "user prompt")
    assert miss2 is None
    print(f"  ✓ Disabled cache returns None")

    # Delete by model
    svc.enabled = True
    svc.set("gpt-4", "sys", "user", "response")
    deleted = svc.delete_by_model("gpt-4")
    assert deleted >= 1
    print(f"  ✓ delete_by_model: {deleted} entries")

    db.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_memory_system_facade():
    """Test the MemorySystem facade and cached_llm creation."""
    print("=== Test 5: MemorySystem facade ===")
    db_path = "test_memory_verify.db"

    # Use a custom db path to avoid cluttering
    import os
    os.environ["MEMORY_DB_PATH"] = db_path
    os.environ["MEMORY_ENABLED"] = "true"
    os.environ["LLM_CACHE_ENABLED"] = "true"

    memory = MemorySystem(db_path=db_path)

    assert memory._enabled, "Memory should be enabled"
    assert memory.db is not None, "Database should be initialized"
    assert memory.cache is not None, "Cache service should be initialized"
    assert memory.cache.enabled, "Cache should be enabled"
    print(f"  ✓ MemorySystem initialized: enabled={memory._enabled}")

    # Test cache stats
    stats = memory.cache.stats()
    print(f"  ✓ Initial cache stats: {stats}")

    # Test cache set/get through the service
    memory.cache.set("test-model", "system", "user", "hello world")
    response = memory.cache.get("test-model", "system", "user")
    assert response == "hello world"
    print(f"  ✓ Cache through facade: '{response}'")

    memory.close()

    # Test disabled memory
    memory2 = MemorySystem(db_path=db_path, enabled=False)
    assert not memory2._enabled
    assert memory2.cache is None
    print(f"  ✓ Disabled memory: cache={memory2.cache}")

    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_config_fields():
    """Test that config has all new memory fields."""
    print("=== Test 6: Config fields ===")
    from src.utils.config import Settings

    s = Settings()

    assert hasattr(s, "memory_db_path"), "memory_db_path missing"
    assert hasattr(s, "memory_enabled"), "memory_enabled missing"
    assert hasattr(s, "llm_cache_enabled"), "llm_cache_enabled missing"
    assert hasattr(s, "llm_cache_ttl_hours"), "llm_cache_ttl_hours missing"
    assert hasattr(s, "embedding_model_name"), "embedding_model_name missing"
    assert hasattr(s, "vector_store_path"), "vector_store_path missing"

    print(f"  ✓ memory_db_path = {s.memory_db_path}")
    print(f"  ✓ memory_enabled = {s.memory_enabled}")
    print(f"  ✓ llm_cache_enabled = {s.llm_cache_enabled}")
    print(f"  ✓ llm_cache_ttl_hours = {s.llm_cache_ttl_hours}")
    print(f"  ✓ embedding_model_name = '{s.embedding_model_name}'")
    print(f"  ✓ vector_store_path = {s.vector_store_path}")
    print("  PASSED\n")


def test_workflow_with_memory():
    """Test that the workflow can be created with memory."""
    print("=== Test 7: Workflow with memory ===")

    # Check if API key is configured
    from src.utils.config import settings
    provider = settings.llm_provider.lower()
    has_api_key = False
    if provider == "deepseek":
        has_api_key = bool(settings.deepseek_api_key and
                          settings.deepseek_api_key != "your_deepseek_api_key")
    elif provider == "qwen":
        has_api_key = bool(settings.llm_api_key and
                          settings.llm_api_key != "your_qwen_api_key")
    elif provider == "openai":
        has_api_key = bool(settings.openai_api_key)

    if not has_api_key:
        print("  ⏭ SKIPPED: No API key configured. Set DEEPSEEK_API_KEY or equivalent.")
        return

    db_path = "test_memory_verify.db"
    memory = MemorySystem(db_path=db_path)

    from src.workflow.research_workflow import ResearchWorkflow

    workflow = ResearchWorkflow(include_full_analysis=False, memory_system=memory)
    assert workflow.memory is memory
    assert workflow.planner.llm is not None
    print(f"  ✓ Workflow created with memory")

    # Test without memory
    workflow2 = ResearchWorkflow(include_full_analysis=False)
    assert workflow2.memory is None
    print(f"  ✓ Workflow created without memory (backward compatible)")

    memory.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_session_repo():
    """Test session repository CRUD."""
    print("=== Phase 2 — Test 8: Session repository ===")
    db_path = "test_memory_verify.db"
    db = Database(db_path)
    db.init_schema()

    from src.memory.repositories.session_repo import SessionRepo
    repo = SessionRepo(db)

    sid = repo.create("sess-1", "multi-task learning")
    assert repo.get(sid) is not None
    assert repo.get(sid)["status"] == "running"
    print(f"  ✓ Create session: {sid}")

    assert repo.complete(sid, summary="Done", paper_count=5)
    assert repo.get(sid)["status"] == "completed"
    print(f"  ✓ Complete session")

    sid2 = repo.create("sess-2", "reinforcement learning")
    assert repo.fail(sid2, error="timeout")
    assert repo.get(sid2)["status"] == "failed"
    print(f"  ✓ Fail session with error")

    sessions = repo.list_by_user(limit=10)
    assert len(sessions) == 2
    print(f"  ✓ List sessions: {len(sessions)}")

    assert repo.delete(sid2)
    assert repo.get(sid2) is None
    print(f"  ✓ Delete session")

    db.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_working_memory_repo():
    """Test working memory repository."""
    print("=== Phase 2 — Test 9: Working memory repository ===")
    db_path = "test_memory_verify.db"
    db = Database(db_path)
    db.init_schema()

    from src.memory.repositories.session_repo import SessionRepo
    from src.memory.repositories.working_memory_repo import WorkingMemoryRepo

    srepo = SessionRepo(db)
    sid = srepo.create("sess-wm", "test")

    wm = WorkingMemoryRepo(db)
    wm.record(sid, "plan", "planner", 1, "topic: test", "3 keywords, 2 subtopics")
    wm.record(sid, "research", "researcher", 2, "keywords: [...]", "10 papers found")
    wm.record(sid, "read", "reader", 3, "10 papers", "10 analyses done")

    timeline = wm.timeline(sid)
    assert len(timeline) == 3
    assert timeline[0]["node_name"] == "plan"
    assert timeline[2]["node_name"] == "read"
    print(f"  ✓ Timeline: {[t['node_name'] for t in timeline]}")

    assert wm.delete_by_session(sid) == 3
    assert len(wm.timeline(sid)) == 0
    print(f"  ✓ Delete by session")

    db.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_session_service():
    """Test session service through MemorySystem."""
    print("=== Phase 2 — Test 10: Session service ===")
    db_path = "test_memory_verify.db"
    memory = MemorySystem(db_path=db_path)

    assert memory.session is not None
    assert memory.working_memory is not None
    print(f"  ✓ Session service initialized")
    print(f"  ✓ Working memory service initialized")

    sid = memory.session.create("sess-svc", "computer vision")
    assert memory.session.get(sid) is not None

    memory.session.complete(sid, "research completed", paper_count=8)
    s = memory.session.get(sid)
    assert s["status"] == "completed"
    assert s["paper_count"] == 8
    print(f"  ✓ Session create -> complete -> verify")

    recent = memory.session.list_recent(limit=5)
    assert len(recent) >= 1
    print(f"  ✓ List recent: {len(recent)} sessions")

    memory.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_session_with_timeline():
    """Test full session + working memory timeline."""
    print("=== Phase 2 — Test 11: Session + Timeline ===")
    db_path = "test_memory_verify.db"
    memory = MemorySystem(db_path=db_path)

    sid = memory.session.create("sess-full", "transformer architectures")

    memory.working_memory.record(sid, "plan", "planner", 1, "topic: transformer", "5 keywords")
    memory.working_memory.record(sid, "research", "researcher", 2, "5 keywords", "8 papers")
    memory.working_memory.record(sid, "read", "reader", 3, "8 papers", "8 analyses")
    memory.working_memory.record(sid, "gap_analysis", "gap", 4, "8 analyses", "3 gaps")
    memory.working_memory.record(sid, "critic", "critic", 5, "3 gaps", "confidence=4")
    memory.working_memory.record(sid, "solution", "solution", 6, "3 gaps", "approach: novel")
    memory.working_memory.record(sid, "experiment", "experiment", 7, "solution", "3 datasets")
    memory.working_memory.record(sid, "package", "package", 8, "results", "2 files")

    memory.session.complete(sid, "transformer study done", paper_count=8)

    timeline = memory.working_memory.timeline(sid)
    assert len(timeline) == 8
    print(f"  ✓ Full 8-step timeline recorded")

    summary = memory.working_memory.summary(sid, last_n=3)
    assert "experiment" in summary and "package" in summary
    print(f"  ✓ Summary (last 3):\n    {summary.replace(chr(10), chr(10)+'    ')}")

    memory.session.delete(sid)
    assert memory.session.get(sid) is None
    assert len(memory.working_memory.timeline(sid)) == 0
    print(f"  ✓ Cascade delete: session + timeline wiped")

    memory.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_knowledge_repo():
    """Test analysis repository with FTS5 search."""
    print("=== Phase 3 — Test 12: Knowledge repository + FTS ===")
    db_path = "test_memory_verify.db"
    db = Database(db_path)
    db.init_schema()

    from src.memory.repositories.analysis_repo import AnalysisRepo
    repo = AnalysisRepo(db)

    # Insert sample analyses
    repo.save("s1", "Attention Is All You Need",
              problem="RNN sequential processing is slow",
              method="Multi-head self-attention mechanism",
              dataset="WMT 2014",
              contribution="Introduced the Transformer architecture for sequence modeling")
    repo.save("s1", "BERT: Pre-training of Deep Bidirectional Transformers",
              problem="Unidirectional context limits representation",
              method="Masked language modeling with bidirectional transformer",
              dataset="BooksCorpus + English Wikipedia",
              contribution="Bidirectional pre-training for deep language understanding")
    repo.save("s2", "GPT-3: Language Models are Few-Shot Learners",
              problem="Task-specific fine-tuning requires labeled data",
              method="Scaling up autoregressive language model to 175B parameters",
              dataset="Common Crawl filtered",
              contribution="Demonstrated few-shot learning at scale with language models")
    print(f"  ✓ Saved 3 paper analyses")

    # Search for a term present in multiple papers
    results = repo.search("language", limit=5)
    assert len(results) >= 2
    titles = [r["paper_title"] for r in results]
    print(f"  ✓ FTS 'language' → {len(results)} results: {titles}")

    # Single paper match
    results = repo.search("attention", limit=5)
    assert len(results) >= 1
    print(f"  ✓ FTS 'attention' → {len(results)} result(s)")

    # Single match for a specific term
    results = repo.search("transformer", limit=5)
    assert len(results) >= 1
    print(f"  ✓ FTS 'transformer' → {len(results)} result(s)")

    # No match
    results = repo.search("quantum computing", limit=5)
    assert len(results) == 0
    print(f"  ✓ FTS 'quantum computing' → 0 results (expected)")

    # No match
    results = repo.search("quantum computing", limit=5)
    assert len(results) == 0
    print(f"  ✓ FTS 'quantum computing' → 0 results (expected)")

    # By title
    row = repo.get_by_title("BERT: Pre-training of Deep Bidirectional Transformers")
    assert row is not None
    assert "bidirectional" in row["method"].lower()
    print(f"  ✓ Get by title: {row['paper_title'][:50]}...")

    # By session
    by_session = repo.list_by_session("s1")
    assert len(by_session) == 2
    print(f"  ✓ Session s1 has {len(by_session)} papers")

    db.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_knowledge_service():
    """Test knowledge service through MemorySystem."""
    print("=== Phase 3 — Test 13: Knowledge service ===")
    db_path = "test_memory_verify.db"
    memory = MemorySystem(db_path=db_path)

    assert memory.knowledge is not None
    print(f"  ✓ Knowledge service initialized")

    # Save through service
    analysis = {
        "title": "ResNet: Deep Residual Learning",
        "url": "https://arxiv.org/abs/1512.03385",
        "problem": "Deep networks suffer from degradation",
        "method": "Residual learning with skip connections",
        "dataset": "ImageNet",
        "metric": "Top-1/Top-5 accuracy",
        "results": {"Top-1": "improved by 3.5%"},
        "limitation": "Requires careful architecture design",
        "contribution": "Enabled training of very deep networks (152 layers)",
    }
    memory.knowledge.save_analysis("sess-kb", "ResNet: Deep Residual Learning", analysis)

    analysis2 = {
        "title": "DenseNet: Densely Connected Convolutional Networks",
        "url": "https://arxiv.org/abs/1608.06993",
        "problem": "Gradient vanishing in deep networks",
        "method": "Dense connectivity pattern between layers",
        "dataset": "CIFAR-10, CIFAR-100, ImageNet",
        "metric": "Classification error rate",
        "results": {"CIFAR-10 error": "3.46%"},
        "limitation": "Memory-intensive due to feature concatenation",
        "contribution": "Introduced dense connections for feature reuse",
    }
    memory.knowledge.save_analysis("sess-kb", "DenseNet: Densely Connected Convolutional Networks", analysis2)

    # Save one more
    memory.knowledge.save_analysis("sess-kb2", "Random Paper About RL", {
        "title": "Random Paper About RL",
        "problem": "Exploration in reinforcement learning",
        "method": "Novel curiosity-driven exploration",
        "dataset": "Atari games",
        "contribution": "Better exploration strategy",
    })

    assert memory.knowledge.total() == 3
    print(f"  ✓ Total papers: {memory.knowledge.total()}")

    # Search
    results = memory.knowledge.search("deep", limit=5)
    assert len(results) >= 2
    print(f"  ✓ Search 'deep' → {len(results)} papers")

    results = memory.knowledge.search("reinforcement", limit=5)
    assert len(results) == 1
    print(f"  ✓ Search 'reinforcement' → {len(results)} paper")

    # By session
    sess_papers = memory.knowledge.list_by_session("sess-kb")
    assert len(sess_papers) == 2
    print(f"  ✓ Session sess-kb papers: {len(sess_papers)}")

    memory.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


def test_vector_store_disabled():
    """Test vector store in disabled mode (no embedding model)."""
    print("=== Phase 4 — Test 14: Vector store (disabled) ===")
    from src.memory.vector_store import VectorStore
    store = VectorStore(store_path="/tmp/test_vs", embedding_model="")
    assert not store.enabled
    assert store.size == 0
    assert store.search("anything") == []
    assert store.add(["text"], [{}]) == 0
    print(f"  ✓ Disabled store: enabled={store.enabled}, size={store.size}")
    print("  PASSED\n")


def test_vector_store_faiss_raw():
    """Test FAISS operations directly with numpy (no embedding API needed)."""
    print("=== Phase 4 — Test 15: FAISS raw operations ===")
    import faiss
    import numpy as np

    dim = 128
    index = faiss.IndexFlatIP(dim)

    # Add 3 random vectors
    np.random.seed(42)
    vecs = np.random.randn(3, dim).astype(np.float32)
    faiss.normalize_L2(vecs)
    index.add(vecs)
    assert index.ntotal == 3
    print(f"  ✓ Index created: {index.ntotal} vectors, dim={dim}")

    # Search with a known vector
    query = vecs[0:1].copy()
    scores, indices = index.search(query, k=2)
    assert indices[0][0] == 0  # closest should be itself
    assert scores[0][0] > 0.99  # cosine ~1.0 for identical vector
    print(f"  ✓ Self-search: top match idx={indices[0][0]}, score={scores[0][0]:.4f}")

    # Save and reload
    faiss.write_index(index, "/tmp/test_faiss.index")
    loaded = faiss.read_index("/tmp/test_faiss.index")
    assert loaded.ntotal == 3
    print(f"  ✓ Save/load: {loaded.ntotal} vectors")

    Path("/tmp/test_faiss.index").unlink(missing_ok=True)
    print("  PASSED\n")


def test_knowledge_semantic_fallback():
    """Test semantic search falls back to FTS when vector store is disabled."""
    print("=== Phase 4 — Test 16: Semantic search fallback ===")
    db_path = "test_memory_verify.db"
    memory = MemorySystem(db_path=db_path)

    # Save papers
    memory.knowledge.save_analysis("s1", "Test Paper 1", {
        "title": "Test Paper 1",
        "problem": "gradient vanishing",
        "method": "residual connections",
        "contribution": "enabled deep networks",
    })
    memory.knowledge.save_analysis("s1", "Test Paper 2", {
        "title": "Test Paper 2",
        "problem": "overfitting in small datasets",
        "method": "dropout regularization",
        "contribution": "simple effective regularization",
    })

    # Semantic search should fall back to FTS
    results = memory.knowledge.search_semantic("deep networks", limit=5)
    assert len(results) >= 1
    print(f"  ✓ Semantic (FTS fallback): {len(results)} results")

    # FTS still works directly
    fts_results = memory.knowledge.search("dropout", limit=5)
    assert len(fts_results) == 1
    print(f"  ✓ FTS direct: {len(fts_results)} result")

    memory.close()
    Path(db_path).unlink(missing_ok=True)
    print("  PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1-4 Verification: Memory System")
    print("=" * 60 + "\n")

    test_database_init()
    test_models()
    test_cache_repo()
    test_cache_service()
    test_memory_system_facade()
    test_config_fields()
    test_workflow_with_memory()
    test_session_repo()
    test_working_memory_repo()
    test_session_service()
    test_session_with_timeline()
    test_knowledge_repo()
    test_knowledge_service()
    test_vector_store_disabled()
    test_vector_store_faiss_raw()
    test_knowledge_semantic_fallback()

    print("=" * 60)
    print("All tests PASSED! Phase 1-4 ready.")
    print("=" * 60)
