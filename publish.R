# One-click publish script for Posit Cloud Connect with AI Changelog & Git Push
root_dir <- getwd()
book_dir <- file.path(root_dir, "_book")

# Step 1: Run AI changelog check & automatic git commit/push
message("========================================")
message("Step 1: Running AI Changelog & Git Sync...")
message("========================================")
py_script <- file.path(root_dir, "scripts", "auto_changelog.py")
if (file.exists(py_script)) {
  system2("python3", args = c(py_script, "--git-sync"))
} else {
  message("[WARN] scripts/auto_changelog.py not found, skipping AI changelog.")
}

# Step 2: Build multilingual books (quarto render zh & en)
message("\n========================================")
message("Step 2: Building books with latest updates...")
message("========================================")
source("build.R")

# Step 3: Deploy to Posit Cloud Connect
message("\n========================================")
message("Step 3: Publishing to Posit Cloud Connect...")
message("========================================")

if (!requireNamespace("rsconnect", quietly = TRUE)) {
  stop("Package 'rsconnect' is not installed. Please install it with: install.packages('rsconnect')")
}

rsconnect::deployApp(
  appDir = book_dir,
  appName = "psych_stats_unhurried",
  appTitle = "心理统计枕边书",
  server = "connect.posit.cloud",
  account = "linwz",
  upload = TRUE
)

message("\n[SUCCESS] Successfully published to Posit Cloud Connect & synced with GitHub!")
message("Book URL: https://linwz-psychstats.share.connect.posit.cloud/")
