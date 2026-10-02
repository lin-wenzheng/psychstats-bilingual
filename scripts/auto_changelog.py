#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Changelog & Git Push Script for Psychological Statistics for the Unhurried People
Author: Lin Wenzheng / Assistant
"""

import os
import sys
import json
import re
import subprocess
import datetime
import urllib.request
import urllib.error

# Configuration
API_URL = "https://ai2api.diedye.org.es/v1/chat/completions"
API_KEY = "qwe123asdQ"
MODEL_NAME = "gemini-flash-latest"
TAG_NAME = "last-published"

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_cmd(cmd, cwd=ROOT_DIR, check=True):
    """Run shell command and return stdout string."""
    env = os.environ.copy()
    if "HOME" not in env or not env["HOME"]:
        env["HOME"] = "/root"
    # Ensure git always trusts the directory
    if cmd.strip().startswith("git "):
        cmd = cmd.strip().replace("git ", "git -c safe.directory='*' ", 1)
    res = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({cmd}):\n{res.stderr.strip()}")
    return res.stdout.strip()

def get_git_diff():
    """Get the relevant diff of .qmd files compared to last-published or HEAD."""
    # Check if last-published tag exists
    tags = run_cmd("git tag -l", check=False).splitlines()
    has_tag = TAG_NAME in tags
    
    base_ref = TAG_NAME if has_tag else "HEAD~1"
    
    # Check if base_ref is a valid git object, fallback to empty/staged if needed
    is_valid_base = False
    if has_tag:
        is_valid_base = True
    else:
        # Check if HEAD~1 exists
        res = subprocess.run("git rev-parse --verify HEAD~1", shell=True, cwd=ROOT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            is_valid_base = True

    if is_valid_base:
        diff_cmd = f"git diff {base_ref} -- '*.qmd'"
        diff_files_cmd = f"git diff --name-only {base_ref} -- '*.qmd'"
    else:
        # If brand new repo with only 1 commit or uncommitted changes
        diff_cmd = "git diff HEAD -- '*.qmd'"
        diff_files_cmd = "git diff --name-only HEAD -- '*.qmd'"

    changed_files = [f for f in run_cmd(diff_files_cmd, check=False).splitlines() if f.endswith(".qmd")]
    
    # Also check any untracked or newly added qmd files
    status_output = run_cmd("git status --porcelain -- '*.qmd'", check=False)
    for line in status_output.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[1].endswith(".qmd") and parts[1] not in changed_files:
            changed_files.append(parts[1])

    # Filter out index.qmd from diff analysis so changes to changelog itself don't trigger recursion
    analysis_files = [f for f in changed_files if not f.endswith("index.qmd")]
    
    if not analysis_files:
        return "", []

    # Get combined diff of meaningful content files
    full_diff = run_cmd(diff_cmd + " -- " + " ".join(f"'{f}'" for f in analysis_files), check=False)
    
    # If no diff from git diff (e.g. untracked files), read untracked files partially
    if not full_diff.strip():
        diff_snippets = []
        for f in analysis_files:
            full_path = os.path.join(ROOT_DIR, f)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as fp:
                    content = fp.read()[:4000]
                    diff_snippets.append(f"--- /dev/null\n+++ b/{f}\n@@ New File @@\n{content}")
        full_diff = "\n".join(diff_snippets)

    return full_diff, analysis_files

def query_llm_for_changelog(diff_text, changed_files):
    """Send git diff to Gemini to determine if changes are substantial and generate summaries."""
    # Truncate diff if extremely large to fit context comfortably
    if len(diff_text) > 40000:
        diff_text = diff_text[:40000] + "\n...[Diff Truncated]..."

    today_str = datetime.date.today().strftime("%Y%m%d")
    today_iso = datetime.date.today().strftime("%Y-%m-%d")

    prompt = f"""你是一名严谨且文风幽默的统计学教程（《心理统计枕边书》）技术审订编辑。
请分析以下 Git Diff 文本（涉及的文件为：{', '.join(changed_files)}）。

【任务要求】：
1. 判定本次改动是否包含【实质性修改】（例如：概念重构、公式推导修正或新增、R代码示例变更、章节新增或结构调整）。
   - 如果仅仅是修复错别字、润色个别标点符号、无实质内容的排版微调，请将 has_substantial_changes 设为 false。
   - 如果有实质内容新增或原理修改，请设为 true。
2. 若 has_substantial_changes 为 true：
   - 生成一段符合作者语气（风趣、真诚、清晰）的中文更新摘要 (summary_zh)，格式形如：
     "在第X章中，增加了……；重构了……。"
   - 生成对应的英文更新摘要 (summary_en)。
   - 生成规范简练的 Git Commit Message (commit_message)，采用 Conventional Commits 格式，如:
     "feat(chap5): add detailed interaction modeling and Type III sums of squares"
   - 对每个发生实质变动的文件，提供简明的一句话条目 (chapter_updates)，说明该章具体改了什么。
3. 若 has_substantial_changes 为 false：
   - commit_message 仍需提供规范的提交信息（如 "docs: fix typos and polish wording"）。

请务必只输出标准的合法 JSON，不要包含任何额外的 Markdown 解释或代码块围栏以外的文字。格式如下：
{{
  "has_substantial_changes": true/false,
  "summary_zh": "中文总结条目",
  "summary_en": "英文总结条目",
  "commit_message": "feat(...): ...",
  "chapter_updates": [
    {{
      "file": "zh/chap5.qmd",
      "note_zh": "增加了对Type III平方和与Helmert对比编码的讲解与代码",
      "note_en": "Added explanations and code for Type III sums of squares and Helmert contrast coding"
    }}
  ]
}}

【Git Diff 内容】：
{diff_text}
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            content = resp_data["choices"][0]["message"]["content"].strip()
            # Clean possible markdown fences
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n", "", content)
                content = re.sub(r"\n```$", "", content)
            return json.loads(content)
    except Exception as e:
        print(f"[WARN] Failed to query LLM for changelog: {e}", file=sys.stderr)
        return None

def update_index_files(summary_zh, summary_en):
    """Safely append the new entry inside <!-- AUTO-CHANGELOG-START/END --> in index.qmd files."""
    today_str = datetime.date.today().strftime("%Y%m%d")
    today_iso = datetime.date.today().strftime("%Y-%m-%d")

    # Update zh/index.qmd
    zh_index_path = os.path.join(ROOT_DIR, "zh", "index.qmd")
    if os.path.exists(zh_index_path) and summary_zh:
        with open(zh_index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        pattern = r"(<!-- AUTO-CHANGELOG-START -->)(.*?)(<!-- AUTO-CHANGELOG-END -->)"
        match = re.search(pattern, content, flags=re.DOTALL)
        if match:
            existing_logs = match.group(2).strip()
            new_entry = f"\n\n{today_str}: {summary_zh}"
            # Check if today's entry already recorded to avoid duplicate on re-runs
            if f"{today_str}: {summary_zh}" not in existing_logs:
                updated_block = f"<!-- AUTO-CHANGELOG-START -->\n{existing_logs}{new_entry}\n<!-- AUTO-CHANGELOG-END -->"
                new_content = content[:match.start()] + updated_block + content[match.end():]
                with open(zh_index_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"[OK] Updated {zh_index_path} with new changelog entry.")

    # Update en/index.qmd
    en_index_path = os.path.join(ROOT_DIR, "en", "index.qmd")
    if os.path.exists(en_index_path) and summary_en:
        with open(en_index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        pattern = r"(<!-- AUTO-CHANGELOG-START -->)(.*?)(<!-- AUTO-CHANGELOG-END -->)"
        match = re.search(pattern, content, flags=re.DOTALL)
        if match:
            existing_logs = match.group(2).strip()
            new_entry = f"\n- **{today_iso}**: {summary_en}"
            if f"**{today_iso}**: {summary_en}" not in existing_logs:
                updated_block = f"<!-- AUTO-CHANGELOG-START -->\n{existing_logs}{new_entry}\n<!-- AUTO-CHANGELOG-END -->"
                new_content = content[:match.start()] + updated_block + content[match.end():]
                with open(en_index_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"[OK] Updated {en_index_path} with new changelog entry.")

def update_chapter_callout(file_rel_path, note_text):
    """Insert or update the collapsible chapter revision history callout."""
    full_path = os.path.join(ROOT_DIR, file_rel_path)
    if not os.path.exists(full_path):
        return
    
    today_iso = datetime.date.today().strftime("%Y-%m-%d")
    is_zh = file_rel_path.startswith("zh/")
    callout_title = "## 🕒 本章修订记录" if is_zh else "## 🕒 Chapter Revision History"
    
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    # If callout already exists in the file, append to it
    callout_pattern = r"(:::\s*\{\.callout-note\s+collapse=\"true\"\s+appearance=\"minimal\"\}\s*\n" + re.escape(callout_title) + r"\s*\n)(.*?)(:::)"
    match = re.search(callout_pattern, content, flags=re.DOTALL)
    
    if match:
        body = match.group(2).strip()
        new_item = f"- **{today_iso}**: {note_text}"
        if new_item not in body:
            new_body = f"{body}\n{new_item}\n"
            content = content[:match.start(2)] + new_body + content[match.end(2):]
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[OK] Appended revision record to existing callout in {file_rel_path}")
    else:
        # Insert after the top-level chapter heading `# ...`
        h1_match = re.search(r"^(#\s+[^\n]+)", content, flags=re.MULTILINE)
        if h1_match:
            insert_pos = h1_match.end()
            callout_block = (
                f"\n\n::: {{.callout-note collapse=\"true\" appearance=\"minimal\"}}\n"
                f"{callout_title}\n"
                f"- **{today_iso}**: {note_text}\n"
                f":::\n"
            )
            content = content[:insert_pos] + callout_block + content[insert_pos:]
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[OK] Injected new revision callout into {file_rel_path}")

def git_sync(commit_msg):
    """Add all changes, commit with message, update tag, and push."""
    # Ensure user identity is configured in repo if not globally set
    try:
        current_name = run_cmd("git config user.name", check=False)
        if not current_name:
            run_cmd("git config user.name 'Wenzheng Lin'")
            run_cmd("git config user.email 'linwenzheng@bnu.edu.cn'")
    except Exception:
        pass

    print("\n[GIT] Staging changes...")
    run_cmd("git add -A")
    
    # Check if there are any staged changes
    staged = run_cmd("git status --porcelain")
    if not staged:
        print("[GIT] Working tree clean, nothing to commit.")
        return

    print(f"[GIT] Committing: {commit_msg}")
    run_cmd(f"git commit -m \"{commit_msg}\"")
    
    print(f"[GIT] Updating tag '{TAG_NAME}'...")
    run_cmd(f"git tag -f {TAG_NAME}")

    current_branch = run_cmd("git branch --show-current")
    if not current_branch:
        current_branch = "master"

    print(f"[GIT] Pushing to remote ({current_branch} & tags)...")
    try:
        # Check if GITHUB_TOKEN is available in env
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        remote_url = run_cmd("git remote get-url origin", check=False)
        
        push_cmd = f"git push origin {current_branch}"
        tags_cmd = "git push origin --tags"
        
        if token and remote_url.startswith("https://"):
            clean_url = re.sub(r"^https://([^@]+@)?", "https://", remote_url)
            authed_url = clean_url.replace("https://", f"https://{token}@")
            push_cmd = f"git push {authed_url} {current_branch}"
            tags_cmd = f"git push {authed_url} --tags"

        run_cmd(push_cmd)
        run_cmd(tags_cmd)
        print("[GIT] Successfully pushed to GitHub!")
    except Exception as e:
        print(f"[NOTE] Git push skipped/pending: {e}")
        print(f"[NOTE] Local commit '{commit_msg}' and tag '{TAG_NAME}' created successfully.")
        print(f"[NOTE] You can push manually anytime with: git push origin {current_branch} --tags")

def main():
    sync_to_git = "--git-sync" in sys.argv

    print("========================================")
    print("Auto Changelog & Substantial Diff Check")
    print("========================================")
    
    diff_text, changed_files = get_git_diff()
    
    if not diff_text.strip() or not changed_files:
        print("[INFO] No content modifications detected in .qmd files.")
        if sync_to_git:
            # Check if there are other files to commit
            staged = run_cmd("git status --porcelain")
            if staged:
                git_sync("chore: update build assets and configuration")
        return

    print(f"[INFO] Detected changes in {len(changed_files)} content file(s):")
    for f in changed_files:
        print(f"  - {f}")

    print(f"[AI] Querying Gemini ({MODEL_NAME}) to analyze substantive changes...")
    result = query_llm_for_changelog(diff_text, changed_files)
    
    commit_message = "docs: update manuscript chapters"
    if result:
        has_sub = result.get("has_substantial_changes", False)
        commit_message = result.get("commit_message", commit_message)
        print(f"[AI] Substantial change detected: {has_sub}")
        print(f"[AI] Commit message: {commit_message}")

        if has_sub:
            summary_zh = result.get("summary_zh", "")
            summary_en = result.get("summary_en", "")
            print(f"[AI] Summary (ZH): {summary_zh}")
            print(f"[AI] Summary (EN): {summary_en}")
            
            # 1. Update index pages
            update_index_files(summary_zh, summary_en)
            
            # 2. Update chapter callouts
            for item in result.get("chapter_updates", []):
                f_path = item.get("file", "")
                note_zh = item.get("note_zh", "")
                note_en = item.get("note_en", "")
                if f_path.startswith("zh/") and note_zh:
                    update_chapter_callout(f_path, note_zh)
                elif f_path.startswith("en/") and note_en:
                    update_chapter_callout(f_path, note_en)
    else:
        print("[WARN] LLM evaluation skipped, proceeding with default commit.")

    if sync_to_git:
        git_sync(commit_message)

if __name__ == "__main__":
    main()
