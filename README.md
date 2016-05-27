# Python test script

### Usage

```python
import sample

input_csv = "<path-to-your-input-csv>"
output_csv = "<path-to-your-output-csv>"

downloader = sample.StoreDownloader()
output_data = downloader.process(input_csv, output_csv)
```
