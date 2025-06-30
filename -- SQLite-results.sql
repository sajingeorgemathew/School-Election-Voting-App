-- SQLite
SELECT position, candidate, COUNT(*) AS vote_count
FROM votes
GROUP BY position, candidate
ORDER BY position, vote_count DESC;
