# Build script for Psychological Statistics for the Unhurried People (Multilingual Edition)

root_dir <- getwd()

message("========================================")
message("Building Chinese Edition (zh)...")
message("========================================")
setwd(file.path(root_dir, "zh"))
quarto::quarto_render()
setwd(root_dir)

message("========================================")
message("Building English Edition (en)...")
message("========================================")
setwd(file.path(root_dir, "en"))
quarto::quarto_render()
setwd(root_dir)

message("========================================")
message("Finalizing language router & deployment...")
message("========================================")
if (!dir.exists("_book")) {
  dir.create("_book", recursive = TRUE)
}
file.copy("root_index.html", "_book/index.html", overwrite = TRUE)

# Preserve rsconnect configuration
dir.create(file.path(root_dir, "_book/rsconnect/connect.posit.cloud/linwz"), recursive = TRUE, showWarnings = FALSE)
if (file.exists(file.path(root_dir, "rsconnect/connect.posit.cloud/linwz/psych_stats_unhurried.dcf"))) {
  file.copy(
    file.path(root_dir, "rsconnect/connect.posit.cloud/linwz/psych_stats_unhurried.dcf"),
    file.path(root_dir, "_book/rsconnect/connect.posit.cloud/linwz/psych_stats_unhurried.dcf"),
    overwrite = TRUE
  )
}

# Define publish function in GlobalEnv so user can run publish() right away
publish <<- function() {
  source("publish.R")
}

message("\n[SUCCESS] Multilingual build finished!")
message("Both books rendered into '_book/zh/' and '_book/en/' with independent sidebars.")
message("To deploy with RStudio GUI, run in console: publish() or source('publish.R')")
