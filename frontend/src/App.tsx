import { useState } from "react";
import SearchBar from "./components/SearchBar.tsx";
import AnswerCard from "./components/AnswerCard.tsx";
import SourceList from "./components/SourceList.tsx";
import type { Source, SearchResponse } from "./types.ts";

function App() {
    const [answer, setAnswer] = useState<string>("");
    const [sources, setSources] = useState<Source[]>([]);
    const [loading, setLoading] = useState<boolean>(false);

    async function handleSearch(question: string): Promise<void> {
        setLoading(true);
        setAnswer("");
        setSources([]);

        const response = await fetch("/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, top_k: 5 }),
        });

        const data: SearchResponse = await response.json();
        setAnswer(data.answer);
        setSources(data.sources);
        setLoading(false);
    }

    return (
        <div>
            <h1>arXiv RAG</h1>
            <SearchBar onSearch={handleSearch} loading={loading} />
            <AnswerCard answer={answer} />
            <SourceList sources={sources} />
        </div>
    );
}

export default App;
