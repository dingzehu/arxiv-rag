import { useState } from "react";

interface SearchBarProps {
    onSearch: (question: string) => void;
    loading: boolean;
}

function SearchBar({ onSearch, loading }: SearchBarProps) {
    const [question, setQuestion] = useState<string>("");

    function handleClick(): void {
        if (question.trim()) {
            onSearch(question.trim());
        }
    }

    function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>): void {
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
