if exists("b:current_syntax")
    finish
endif

syntax keyword swipcKeywords interface type is

syntax match swipcDocComment "\v#.*$"
syntax match swipcComment "\v//.*$"

syntax match swipcDecorator "@" display nextgroup=swipcName skipwhite
syntax match swipcName "[a-zA-Z_][a-zA-Z0-9_]*\%(\.[a-zA-Z_][a-zA-Z0-9_]*\)*" display contained

highlight link swipcKeywords Keyword
highlight link swipcComment Comment
highlight link swipcDocComment SpecialComment

highlight link swipcDecorator Define
highlight link swipcName Function

let b:current_syntax = "swipc"
