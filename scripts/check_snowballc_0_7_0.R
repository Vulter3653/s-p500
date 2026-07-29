script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_arg) != 1L) stop("Cannot determine this script's path.")
script_path <- normalizePath(sub("^--file=", "", script_arg), mustWork = TRUE)
repo_root <- normalizePath(file.path(dirname(script_path), ".."), mustWork = TRUE)
target_library <- file.path(
  repo_root, "references", "software", "r_library", "snowballc_0_7_0"
)
metadata_directory <- file.path(
  repo_root, "references", "software", "r_snowballc_environment"
)

if (!dir.exists(target_library)) stop("Pinned SnowballC library does not exist.")
if (!requireNamespace("SnowballC", quietly = TRUE, lib.loc = target_library)) {
  stop("SnowballC is not installed in the pinned library.")
}
actual_version <- as.character(packageVersion("SnowballC", lib.loc = target_library))
if (!identical(actual_version, "0.7.0")) {
  stop("Expected SnowballC 0.7.0 but found ", actual_version)
}

words <- c("organization", "technology", "performance", "physics", "science", "subject")
stems <- SnowballC::wordStem(words, language = "porter")
if (length(stems) != length(words)) stop("wordStem output length differs from input.")
if (anyNA(stems)) stop("wordStem returned NA.")
if (any(!nzchar(stems))) stop("wordStem returned an empty stem.")

dir.create(metadata_directory, recursive = TRUE, showWarnings = FALSE)
session_file <- file.path(metadata_directory, "session_info.txt")
session_lines <- trimws(capture.output(sessionInfo()), which = "right")
writeLines(session_lines, session_file, useBytes = TRUE)

cat("validation_status=PASS\n")
cat("R_version=", R.version.string, "\n", sep = "")
cat("platform=", R.version$platform, "\n", sep = "")
cat("SnowballC_version=", actual_version, "\n", sep = "")
cat("library_path=references/software/r_library/snowballc_0_7_0\n")
cat("input_word_count=", length(words), "\n", sep = "")
cat("output_stem_count=", length(stems), "\n", sep = "")
cat("na_count=", sum(is.na(stems)), "\n", sep = "")
cat("empty_stem_count=", sum(!nzchar(stems)), "\n", sep = "")
cat("wordStem_status=PASS\n")
