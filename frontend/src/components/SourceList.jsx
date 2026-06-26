function SourceList({ sources }) {
    if (!sources || sources.length === 0) return null;

    return (
        <div>
            <h2>Sources</h2>
            {sources.map((source) => (
                <div key={source.arxiv_id}>
                    <strong>{source.title}</strong>
                    <span> — {source.authors}</span>
                    <span> | arXiv: {source.arxiv_id}</span>
                    <span> | Score: {(source.similarity_score * 100).toFixed(0)}%</span>
                </div>
            ))}
        </div>
    );
}

export default SourceList;