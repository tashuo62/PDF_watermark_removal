document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const selectFileBtn = document.getElementById('select-file-btn');
    const processBtn = document.getElementById('process-btn');
    const previewBtn = document.getElementById('preview-btn');
    const clearBtn = document.getElementById('clear-btn');
    const message = document.getElementById('message');
    const downloadLink = document.getElementById('download-link');
    const progressBar = document.getElementById('progress-bar');
    const progress = document.getElementById('progress');
    const previewModal = document.getElementById('preview-modal');
    const pdfPreview = document.getElementById('pdf-preview');
    const closePreviewBtn = document.getElementById('close-preview-btn');
    const dropZone = document.getElementById('drop-zone');

    let previewUrl = null;
    let processed = false;

    selectFileBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0 && fileInput.files[0].type === 'application/pdf') {
            processBtn.disabled = false;
            clearBtn.disabled = false;
            message.textContent = '已选择文件，点击处理';
            previewUrl = URL.createObjectURL(fileInput.files[0]);
            const fileName = fileInput.files[0].name;
            document.getElementById('selected-file').textContent = `已选择文件：${fileName}`;
            document.getElementById('selected-file').classList.remove('hidden');
        } else {
            message.textContent = '请选择一个 PDF 文件';
            resetState();
        }
    });

    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        dropZone.classList.remove('dragover');
        const files = event.dataTransfer.files;
        if (files.length > 0 && files[0].type === 'application/pdf') {
            fileInput.files = files;
            processBtn.disabled = false;
            clearBtn.disabled = false;
            message.textContent = '已选择文件，点击处理';
            previewUrl = URL.createObjectURL(files[0]);
            const fileName = files[0].name;
            document.getElementById('selected-file').textContent = `已选择文件：${fileName}`;
            document.getElementById('selected-file').classList.remove('hidden');
        } else {
            message.textContent = '请拖放一个 PDF 文件';
            resetState();
        }
    });

    processBtn.addEventListener('click', async () => {
        if (!fileInput.files.length) return;

        processBtn.disabled = true;
        clearBtn.disabled = true; // 禁用清除按钮
        processBtn.textContent = '处理中...';
        progressBar.classList.remove('hidden');
        progress.style.width = '0%';

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const uploadResponse = await fetch('/upload', { method: 'POST', body: formData });
            const uploadData = await uploadResponse.json();
            if (uploadData.message !== '文件上传成功') {
                message.textContent = '上传失败';
                resetProcessing();
                return;
            }

            progress.style.width = '20%';
            message.textContent = '文件上传成功，正在处理...';

            const removeResponse = await fetch('/remove_watermark');
            const reader = removeResponse.body.getReader();
            let totalPages = 0;
            let decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (!line.trim()) continue;
                    console.log('Raw line:', line);
                    const data = JSON.parse(line);
                    console.log('Parsed data:', data);
                    if (!data.completed) {
                        totalPages = data.total_pages || totalPages;
                        const currentPage = data.current_page;
                        if (currentPage === undefined || totalPages === 0) {
                            console.error('Invalid data:', data);
                            message.textContent = '处理数据错误';
                            resetProcessing();
                            return;
                        }
                        const progressPercent = 20 + (currentPage / totalPages) * 80;
                        console.log(`Page ${currentPage}/${totalPages}, Progress: ${progressPercent}%`);
                        requestAnimationFrame(() => {
                            progress.style.width = `${progressPercent}%`;
                        });
                        message.textContent = data.message;
                    } else {
                        processBtn.textContent = '已处理';
                        message.textContent = '水印去除成功';
                        requestAnimationFrame(() => {
                            progress.style.width = '100%';
                        });
                        downloadLink.classList.remove('hidden');
                        downloadLink.classList.add('fade-in');
                        previewBtn.classList.remove('hidden');
                        previewBtn.classList.add('fade-in');
                        processed = true;
                        setTimeout(() => progressBar.classList.add('hidden'), 500);
                        // 处理完成后不禁用按钮，保持可用状态
                    }
                }
            }

            if (buffer.trim()) {
                const data = JSON.parse(buffer);
                if (data.completed) {
                    processBtn.textContent = '已处理';
                    message.textContent = '水印去除成功';
                    progress.style.width = '100%';
                    downloadLink.classList.remove('hidden');
                    downloadLink.classList.add('fade-in');
                    previewBtn.classList.remove('hidden');
                    previewBtn.classList.add('fade-in');
                    processed = true;
                    setTimeout(() => progressBar.classList.add('hidden'), 500);
                    // 处理完成后不禁用按钮，保持可用状态
                }
            }
        } catch (error) {
            console.error('Error:', error);
            message.textContent = '处理出错';
            resetProcessing();
        }
    });

    previewBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (processed) {
            pdfPreview.src = '/preview';
            previewModal.classList.add('open');
        }
    });

    closePreviewBtn.addEventListener('click', () => {
        previewModal.classList.remove('open');
    });

    clearBtn.addEventListener('click', () => {
        resetState();
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
            previewUrl = null;
        }
        previewModal.classList.remove('open');
        message.textContent = '已清除文件';
    });

    function resetState() {
        fileInput.value = '';
        processBtn.disabled = true;
        previewBtn.classList.add('hidden');
        clearBtn.disabled = true;
        processBtn.textContent = '处理';
        downloadLink.classList.add('hidden');
        progressBar.classList.add('hidden');
        progress.style.width = '0%';
        processed = false;
        document.getElementById('selected-file').textContent = '';
        document.getElementById('selected-file').classList.add('hidden');
    }

    function resetProcessing() {
        processBtn.disabled = false;
        clearBtn.disabled = false; // 恢复清除按钮
        processBtn.textContent = '处理';
        progressBar.classList.add('hidden');
        progress.style.width = '0%';
    }
});