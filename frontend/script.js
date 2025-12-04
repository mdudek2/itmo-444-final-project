const form = document.getElementById("uploadForm");
const responseBox = document.getElementById("response");

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById("resumeFile");
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    responseBox.textContent = "Uploading...";

    try {
        const res = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        // Show ONLY the parsed JSON
        if (data.parsed_json) {
            responseBox.textContent = JSON.stringify(data.parsed_json, null, 2);
        } else {
            responseBox.textContent = "Upload succeeded, but no JSON returned.";
        }

    } catch (err) {
        responseBox.textContent = "Error: " + err.message;
    }
});

