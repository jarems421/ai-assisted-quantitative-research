"""Source Retrieval V001: one owner-authorised, exact-URL original-source retrieval attempt per request.

Subordinate to the campaign controller: it never schedules, retries, resumes or calls another component,
writes no human record and authorises nothing. Docs: docs/source_retrieval_v001.md.
"""
VERSION = 'SOURCE_RETRIEVAL_V001'
