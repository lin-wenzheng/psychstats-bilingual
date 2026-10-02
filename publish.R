# One-click publish script for Posit Cloud Connect
root_dir <- getwd()
book_dir <- file.path(root_dir, "_book")

if (!dir.exists(book_dir) || !file.exists(file.path(book_dir, "index.html"))) {
  message("Building books first...")
  source("build.R")
}

message("Publishing '_book' to Posit Cloud Connect (https://linwz-psychstats.share.connect.posit.cloud/)...")

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

message("\n[SUCCESS] Successfully published to Posit Cloud Connect!")
message("URL: https://linwz-psychstats.share.connect.posit.cloud/")
