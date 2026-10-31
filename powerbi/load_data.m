// Power Query (M): Home > Get Data > Blank Query > Advanced Editor. Paste this, set DataFolder, then create one query per table.
let
    DataFolder = "C:\path\to\student-performance-analytics\powerbi\data\",
    Load = (name as text) =>
        let
            Source  = Csv.Document(File.Contents(DataFolder & name & ".csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
            Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
            Typed   = Table.TransformColumnTypes(Headers, {})
        in
            Typed,
    // Example: dim_student = Load("dim_student")
    dim_student = Load("dim_student")
in
    dim_student
