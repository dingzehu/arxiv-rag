export interface Source {
    arxiv_id: string;
    title: string;
    authors: string;
    similarity_score: number;
}

export interface SearchResponse {
    answer: string;
    sources: Source[];
}
