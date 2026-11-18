# Batch Preprocessing Design – POJ-104

## 1. Objective

This document defines the batch preprocessing strategy for processing all 52,000 source files in the POJ-104 dataset.

The batch processor will reuse the source reader implemented in Checkpoint 2.5.2.

## 2. Processing Strategy

The project will initially use sequential batch processing.

Each source file will be processed independently to ensure:
- Simple error handling.
- Reproducible results.
- Easy debugging.
- No interruption of the entire batch when one file fails.

Multiprocessing may be considered in future optimization stages.

## 3. Input and Output

**Input:**

`data/raw/poj104/ProgramData/`

**Output:**

`data/processed/poj104/source/`

The original problem directory and filename must be preserved.

Example:

| Raw Path | Processed Path |
|---|---|
| `ProgramData/26/345.txt` | `source/26/345.txt` |
| `ProgramData/62/593.txt` | `source/62/593.txt` |

## 4. Batch Processing Workflow

1. Discover all `.txt` source files recursively.
2. Determine each file's relative path.
3. Read the source using `read_source_file()`.
4. Normalize source text according to the preprocessing policy.
5. Create the corresponding output directory.
6. Save the processed source using UTF-8.
7. Record the processing result.
8. Continue to the next file.
9. Generate a batch processing report.

## 5. Error Handling

If a file cannot be read or decoded:
- Record its path and error message.
- Mark it as failed.
- Continue processing the remaining files.
- Never modify or delete the original file.

## 6. Output Management

The processor must:
- Create missing output directories automatically.
- Preserve problem IDs and original filenames.
- Overwrite existing processed files when rerunning the pipeline.
- Avoid modifying files under the raw dataset directory.

## 7. Processing Statistics

The batch report will include:

- Total discovered files.
- Successful files.
- Failed files.
- Encoding distribution.
- Total original file size.
- Total processed file size.
- Processing duration.

Detailed per-file metadata will be implemented in Checkpoint 2.6.

## 8. Validation Requirements

The batch processor must satisfy the following conditions:

1. Every discovered file has a recorded processing result.
2. Successful files have corresponding processed outputs.
3. Failed files are recorded with error details.
4. Output paths preserve the original directory structure.
5. Processed files can be decoded using UTF-8.
6. Raw files remain unchanged.
7. The batch report accurately reflects the processing results.

## 9. Future Reusability

The source reader and normalization logic should remain independent of POJ-104 directory structure.

This allows the same preprocessing functionality to be reused for source files uploaded through the teacher-facing web application.

---

**Status:** Design completed  
**Stage:** Dataset – Checkpoint 2.5.3.1  
**Next:** Checkpoint 2.5.3.2 – Implement Batch Processor