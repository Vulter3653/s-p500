options(repos = c(CRAN = "https://cloud.r-project.org"), timeout = 120)

script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_arg) != 1L) stop("Cannot determine this script's path.")
script_path <- normalizePath(sub("^--file=", "", script_arg), mustWork = TRUE)
repo_root <- normalizePath(file.path(dirname(script_path), ".."), mustWork = TRUE)
target_library <- file.path(
  repo_root, "references", "software", "r_library", "snowballc_0_7_0"
)
cache_directory <- file.path(target_library, ".source-cache")
archive_path <- file.path(cache_directory, "SnowballC_0.7.0.tar.gz")
archive_url <- paste0(
  "https://cran.r-project.org/src/contrib/Archive/",
  "SnowballC/SnowballC_0.7.0.tar.gz"
)
expected_archive_sha256 <- "b10fee9d322f567a22c580b49b5d4ba1c86eae40a71794ca92552c726b3895f3"

dir.create(target_library, recursive = TRUE, showWarnings = FALSE)
dir.create(cache_directory, recursive = TRUE, showWarnings = FALSE)

sha256_file <- function(path) {
  output <- system2("sha256sum", path, stdout = TRUE, stderr = TRUE)
  status <- attr(output, "status")
  if (!is.null(status) && status != 0L) stop("sha256sum failed: ", paste(output, collapse = "\n"))
  strsplit(output[[1]], "[[:space:]]+")[[1]][[1]]
}

valid_gzip <- function(path) {
  con <- file(path, "rb")
  on.exit(close(con))
  identical(as.integer(readBin(con, "raw", n = 2L)), c(31L, 139L))
}

installed_version <- tryCatch(
  as.character(packageVersion("SnowballC", lib.loc = target_library)),
  error = function(e) NA_character_
)

if (identical(installed_version, "0.7.0") && file.exists(archive_path)) {
  message("SnowballC 0.7.0 already installed; skipping installation.")
} else {
  if (!file.exists(archive_path)) {
    temporary_archive <- tempfile(fileext = ".tar.gz")
    on.exit(unlink(temporary_archive), add = TRUE)
    status <- tryCatch(
      download.file(archive_url, temporary_archive, mode = "wb", quiet = FALSE),
      error = function(e) stop("SnowballC archive download failed: ", conditionMessage(e))
    )
    if (!identical(status, 0L)) stop("SnowballC archive download returned status ", status)
    if (!valid_gzip(temporary_archive)) stop("Downloaded file is not a gzip archive.")
    if (file.info(temporary_archive)$size <= 0) stop("Downloaded archive is empty.")
    if (!file.copy(temporary_archive, archive_path, overwrite = FALSE)) {
      stop("Could not place verified archive in the project library cache.")
    }
  }
  if (!valid_gzip(archive_path)) stop("Cached SnowballC archive is not gzip data.")
  archive_sha256 <- sha256_file(archive_path)
  if (!identical(archive_sha256, expected_archive_sha256)) {
    stop("SnowballC archive SHA-256 mismatch: expected ", expected_archive_sha256,
         " but found ", archive_sha256)
  }
  message("Archive SHA-256: ", archive_sha256)
  install.packages(archive_path, repos = NULL, type = "source", lib = target_library)
}

archive_sha256 <- sha256_file(archive_path)
if (!identical(archive_sha256, expected_archive_sha256)) {
  stop("Cached SnowballC archive SHA-256 does not match the pinned value.")
}
actual_version <- as.character(packageVersion("SnowballC", lib.loc = target_library))
if (!identical(actual_version, "0.7.0")) {
  stop("Expected SnowballC 0.7.0 but found ", actual_version)
}

cat("SnowballC version:", actual_version, "\n")
cat("Library path:", file.path("references", "software", "r_library", "snowballc_0_7_0"), "\n")
cat("Installed package path:", find.package("SnowballC", lib.loc = target_library), "\n")
cat("Archive SHA-256:", archive_sha256, "\n")
print(sessionInfo())
