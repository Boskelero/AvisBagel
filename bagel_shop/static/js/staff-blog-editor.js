(function () {
    const form = document.getElementById('staff-blog-form');
    if (!form || !window.CKEDITOR) return;

    const licenseKey = form.dataset.licenseKey;
    const uploadUrl = form.dataset.uploadUrl;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const {
        Alignment, Autoformat, BlockQuote, Bold, ClassicEditor, Essentials, Heading,
        Image, ImageCaption, ImageResize, ImageStyle, ImageToolbar, ImageUpload,
        Italic, Link, List, Paragraph, PasteFromOffice, SimpleUploadAdapter,
        Table, TableToolbar, Undo
    } = window.CKEDITOR;

    document.querySelectorAll('.js-rich-editor').forEach((element) => {
        ClassicEditor.create(element, {
            licenseKey,
            plugins: [
                Alignment, Autoformat, BlockQuote, Bold, Essentials, Heading, Image,
                ImageCaption, ImageResize, ImageStyle, ImageToolbar, ImageUpload,
                Italic, Link, List, Paragraph, PasteFromOffice, SimpleUploadAdapter,
                Table, TableToolbar, Undo
            ],
            toolbar: {
                items: [
                    'undo', 'redo', '|', 'heading', '|', 'bold', 'italic', 'link',
                    'alignment', '|', 'bulletedList', 'numberedList', 'blockQuote',
                    'insertTable', 'uploadImage'
                ],
                shouldNotGroupWhenFull: false
            },
            simpleUpload: {
                uploadUrl,
                headers: { 'X-CSRFToken': csrfToken }
            },
            image: {
                toolbar: [
                    'imageTextAlternative', 'toggleImageCaption', '|',
                    'imageStyle:inline', 'imageStyle:block', 'imageStyle:side'
                ]
            },
            table: { contentToolbar: ['tableColumn', 'tableRow', 'mergeTableCells'] }
        }).then((editor) => {
            if (element.dataset.direction === 'rtl') {
                editor.editing.view.change((writer) => {
                    writer.setAttribute('dir', 'rtl', editor.editing.view.document.getRoot());
                });
            }
        }).catch((error) => {
            console.error('Could not initialize the blog editor.', error);
        });
    });
}());
