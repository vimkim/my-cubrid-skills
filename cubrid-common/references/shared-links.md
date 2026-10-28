# Links in shared material

Apply this rule to JIRA descriptions, PR bodies, reviewer guides, and documents
intended for other readers, including linked explanations. Use URLs accessible
to the intended readers, such as verified GitHub, JIRA, or CI URLs. A successful
request from the author's machine alone does not establish reader access.

The host `dev2.baboon-rudd.ts.net` is a personal viewing service available only
to the user. Keep its URLs in personal chat handoffs; exclude them from shared
material, including images and reference links. Apply the same audience rule to
other personal services. When no suitable shared URL exists, include the essential
evidence inline and omit the private link. Verify a replacement's destination and
contents; inventing a URL or publishing a document is not an automatic repair.

Resolve `link_checker` to this collection's
`cubrid-common/scripts/check-shared-links.py`, then run:

```bash
python3 "$link_checker" "$body_file"
```

Pass additional shared files as further arguments. Check the saved material before
review and immediately before publication. Correct preparation failures and rerun
the check. After approval, validation is read-only: report a failure and return
necessary text changes to review rather than rewriting approved files.

The checker scans all supplied UTF-8 text, including bare URLs, Markdown links,
reference definitions, images, HTML, and code blocks. It rejects the known personal
hostname regardless of case, scheme, port, or path and reports `file:line` with a
nonzero exit status. Missing or unreadable files also fail. It makes no network
requests and does not prove that other URLs are accessible to the intended readers;
review their audience and destination separately.
