function setTitle(){
    var url = window.location.href;
    if (url.indexOf('#') != -1){
        var anchor = url.substring(url.indexOf('#') + 1);
        document.title = "SwIPC | "+anchor;
    }
}

window.onhashchange = setTitle
window.onload = setTitle