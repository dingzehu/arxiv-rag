interface AnswerCardProps {
    answer: string;
}

function AnswerCard({ answer }: AnswerCardProps) {
    if (!answer) return null;

    return (
        <div>
            <h2>Answer</h2>
            <p>{answer}</p>
        </div>
    );
}

export default AnswerCard;
