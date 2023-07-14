window.MathJax = {
    tex: {
        inlineMath: [
            ["\\(", "\\)"],
            ['[mathjaxinline]', '[/mathjaxinline]']
        ],
        displayMath: [
            ["\\[", "\\]"],
            ['[mathjax]', '[/mathjax]']
        ],
        autoload: {
            color: [],
            colorV2: ['color']
        },
        packages: { '[+]': ['noerrors'] }
    },
    options: {
        ignoreHtmlClass: 'tex2jax_ignore',
        processHtmlClass: 'tex2jax_process'
    },
    loader: {
        load: ['input/asciimath', '[tex]/noerrors']
    }
};