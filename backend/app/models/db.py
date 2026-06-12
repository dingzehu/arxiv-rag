from sqlalchemy import Index, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from pgvector.sqlalchemy import Vector
from app.database import Base

class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True)
    arxiv_id: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    authors: Mapped[str] = mapped_column(nullable=False)
    abstract: Mapped[str | None]     # None means the column is nullable
    pdf_url: Mapped[str] = mapped_column(nullable=False)
    published_date: Mapped[date | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"))
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    chunk_text: Mapped[str] = mapped_column(nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)

Index(
    "chunks_embedding_hnsw_idx",     # index name
    Chunk.embedding,        # column to index
    postgresql_using="hnsw",     # index structure
    postgresql_ops={"embedding": "vector_cosine_ops"}   # comparison formular
)

    