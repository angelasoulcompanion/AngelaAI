#!/bin/bash
# Check chunks after upload

echo "📊 Checking document_chunks table..."
echo ""

psql -d AngelaMemory -U davidsamanyaporn -c "
SELECT
    chunk_id,
    LEFT(content, 50) as content_preview,
    content_tokens IS NOT NULL as has_tokens,
    thai_word_count,
    english_word_count,
    has_mixed_language,
    sentence_boundaries IS NOT NULL as has_boundaries,
    embedding_model,
    page_number,
    section_title,
    section_level,
    importance_score,
    readability_score IS NOT NULL as has_readability,
    created_at
FROM document_chunks
ORDER BY created_at DESC
LIMIT 3;
"

echo ""
echo "📚 Total chunks:"
psql -d AngelaMemory -U davidsamanyaporn -c "SELECT COUNT(*) FROM document_chunks;"
