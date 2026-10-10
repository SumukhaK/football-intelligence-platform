# Project website

A compact, static introduction to Football Intelligence Platform, published at
https://fip-ai.dev/.

## Pitch and design

Football analysis you can question and inspect: outcome probabilities,
feature explanations and an assistant backed by retrieval and service tools.
The primary action is the recorded demo; the secondary action is the repository.
The page uses the Android app's green palette, system fonts and a responsive
editorial layout. Navigation works with a keyboard. There is no JavaScript,
analytics, external font or build dependency.

The page describes the working local product. It does not claim a hosted beta,
a Claude integration, customers or guaranteed hallucination prevention.
The serving dataset figures come from the refit report in docs/reports.
The demo and poster are the existing v2.0.0 recording, clearly dated.

## Preview and verify

From the repository root:

    python scripts/check_site.py
    python -m http.server 8080 --directory docs/site

Open http://localhost:8080/. Check at 320, 768, 1024 and 1440 pixels.
Regression tests live in ai/tests/docs/test_site.py.

## Publish

Application source follows the normal PR workflow into develop.
Only the static site's contents are published to gh-pages, so unrelated
documents and application data are not exposed as website files.

Commit site changes first, then run from the repository root:

    python scripts/check_site.py
    git fetch origin gh-pages
    git subtree split --prefix=docs/site --branch=site-publish
    git push --force-with-lease=gh-pages:origin/gh-pages origin site-publish:gh-pages
    git branch -D site-publish

gh-pages holds generated output only, so each publish replaces it. Make every
change in docs/site, never on gh-pages: a commit made there, including the one
GitHub's Pages settings make when the domain changes, is lost on the next publish.

GitHub Pages serves the root of gh-pages with HTTPS.
The .nojekyll file disables Jekyll processing. Publish after site changes;
merging a source PR alone does not republish it. No deployment token is stored.

## Custom domain

The site is served at fip-ai.dev. The CNAME file in docs/site carries the
domain, so every publish keeps it. To change the domain, edit CNAME and the
canonical and social URLs in index.html, update the DNS records, then publish.
A test checks that CNAME and the canonical URL agree.
