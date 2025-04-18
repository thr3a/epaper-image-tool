document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("upload-form");
  const imageInput = document.getElementById("image-input");
  const resultImage = document.getElementById("result-image");
  const downloadButtons = document.getElementById("download-buttons");
  const downloadJpg = document.getElementById("download-jpg");
  const downloadPng = document.getElementById("download-png");
  const downloadBmp = document.getElementById("download-bmp");

  let currentImageBlob = null;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (!imageInput.files.length) return;

    const formData = new FormData();
    formData.append("image", imageInput.files[0]);

    // ボタン無効化
    form.querySelector("button[type=submit]").disabled = true;

    try {
      const res = await fetch("/process", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("画像処理に失敗しました");
      const blob = await res.blob();
      currentImageBlob = blob;
      const url = URL.createObjectURL(blob);
      resultImage.src = url;
      resultImage.classList.remove("d-none");
      downloadButtons.classList.remove("d-none");
    } catch (err) {
      alert(err.message);
    } finally {
      form.querySelector("button[type=submit]").disabled = false;
    }
  });

  function downloadImage(ext) {
    if (!currentImageBlob) return;
    let filename = "epaper_image." + ext;
    fetch(`/download?format=${ext}`)
      .then((res) => {
        if (!res.ok) throw new Error("ダウンロードに失敗しました");
        return res.blob();
      })
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }, 100);
      })
      .catch((err) => {
        alert(err.message);
      });
  }

  downloadJpg.addEventListener("click", function () {
    downloadImage("jpg");
  });
  downloadPng.addEventListener("click", function () {
    downloadImage("png");
  });
  downloadBmp.addEventListener("click", function () {
    downloadImage("bmp");
  });
});
