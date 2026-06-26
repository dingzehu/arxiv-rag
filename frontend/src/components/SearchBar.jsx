import { useState } from "react";

function SearchBar({ onSearch, loading }) {
    const [question, setQuestion] = useState("");

    function handleClick() {
        if (question.trim()) {
            onSearch(question.trim());
        }
    }

    function handleKeyDown(e) {
        if (e.key === "Enter") {
            handleClick();
        }
    }

    return (
        <div>
            <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question about ML papers..."
                disabled={loading}
            />
            <button onClick={handleClick} disabled={loading}>
                {loading ? "Searching..." : "Search"}
            </button>
        </div>
    );
}

export default SearchBar;