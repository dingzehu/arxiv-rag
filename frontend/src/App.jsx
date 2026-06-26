import { useState } from "react";
import SearchBar from "./components/SearchBar.jsx";
import AnswerCard from "./components/AnswerCard.jsx";
import SourceList from "./components/SourceList.jsx";

function App() {
    const [answer, setAnswer] = useState("");
    const [sources, setSources] = useState([]);
    const [loading, setLoading] = useState(false);

    async function handleSearch(question) {
        setLoading(true);
        setAnswer("");
        setSources([]);

        const response = await fetch("/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, top_k: 5 }),
        });

        const data = await response.json();
        setAnswer(data.answer);
        setSources(data.sources);
        setLoading(false);
    }

    return (
        <div>
            <h1>arXiv RAG</h1>
            <SearchBar onSearch={handleSearch} loading={loading} />
            <AnswerCard answer={answer}/>
            <SourceList sources={sources}/>
        </div>
    );
}

export default App;