(function () {
    const form = document.querySelector('.js-rich-editor-form');
    if (!form || !window.CKEDITOR) return;

    const uploadUrl = form.dataset.uploadUrl;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const {
        Alignment, Autoformat, BlockQuote, Bold, ClassicEditor, Essentials, Heading,
        Image, ImageCaption, ImageResize, ImageStyle, ImageToolbar, ImageUpload,
        Italic, Link, List, Paragraph, PasteFromOffice, SimpleUploadAdapter,
        Table, TableToolbar, Undo
    } = window.CKEDITOR;

    const initializeEditor = (element) => {
        if (element.dataset.editorReady === 'true') return;
        element.dataset.editorReady = 'true';
        ClassicEditor.create(element, {
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
            delete element.dataset.editorReady;
            console.error('Could not initialize the rich-text editor.', error);
        });
    };

    const initializeVisibleEditors = (root = document) => {
        root.querySelectorAll('.js-rich-editor').forEach((element) => {
            if (element.offsetParent !== null) initializeEditor(element);
        });
    };

    initializeVisibleEditors();
    document.querySelectorAll('.staff-page-editor').forEach((panel) => {
        panel.addEventListener('toggle', () => {
            if (panel.open) initializeVisibleEditors(panel);
        });
    });
}());
