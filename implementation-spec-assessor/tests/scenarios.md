# Manual behavior scenarios

## COMPARE input contract

Given two prompt versions, require a plain-text source and a distinct source ID for each version. Reject a missing comparison source or an invalid ID before writing any report. Mark empty source text `BLOCKED` and do not calculate deltas from it.

## Refinement limit contract

Given `REFINE_REASSESS`, accept only an integer from 1 through 5. Reject booleans, non-integers, and out-of-range values before assessment. Use 3 when the input is omitted.

## Default output and collision handling

Given no output directory, write to the documented source-ID path. If any target report already exists, return `OUTPUT_CONFLICT` and write no files. For COMPARE, check every target before creating any output subdirectory.
