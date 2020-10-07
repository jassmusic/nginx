<?php 
$filename = $_GET['filename']; 
if (empty($filename)) {
  $filename = 'home';
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/milligram/1.3.0/milligram.min.css">
  <script type="application/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/marked/0.3.19/marked.min.js"></script>
  <style rel="stylesheet">code.error {line-height:2rem;font-size:2rem;color:#F43;padding:2rem;display: block;}</style>
  <script>
    const FILENAME = "https://raw.githubusercontent.com/soju6jan/nginx_support/main/<?php echo $filename; ?>.md";
    const set = (t) => document.getElementById('content').innerHTML = t;
    const pull = fetch(FILENAME, {headers: {'Accept': 'text/markdown'}})
      .then((res) => {
        if (!res.ok)
          throw new Error(`${res.statusText} (${res.status})`);

        return res.text()
      })
  </script>
  <script defer>
    pull.then((text) => set(marked(text)))
      .catch((err) => set(`<code class="error">Failed to load ${FILENAME}: ${err.message}</code>`))
  </script>
</head>
<body>

<div class="container box" style="margin:5rem auto;padding:4rem">
  <div id="content"></div>
</div>

</body>
</html>