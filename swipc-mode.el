(defvar swipc-mode-hook nil)
(defvar swipc-mode-map
  (let ((map (make-sparse-keymap)))
    (define-key map "\C-j" 'newline-and-indent)
    map)
  "Keymap for SwIPC major mode")

;;;###autoload
(add-to-list 'auto-mode-alist '("\\.id\\'" . swipc-mode))

(defconst swipc-type-keywords '("u8" "i8" "u16" "i16" "u32" "i32" "u64" "i64" "u128" "i128" "pid" "bytes" "object" "buffer" "array" "KObject" "align") "Type keywords for SwIPC mode")
(defconst swipc-keywords '("type" "interface" "is" "struct") "Keywords for SwIPC mode")
(defconst swipc-constants '("unknown") "Constants for SwIPC mode")

(defconst swipc-re-types (regexp-opt swipc-type-keywords 'words))
(defconst swipc-re-keywords (regexp-opt swipc-keywords 'words))
(defconst swipc-re-constants (regexp-opt swipc-constants 'words))

(defconst swipc-mode-syntax-table
  (let ((st (make-syntax-table)))
    (modify-syntax-entry ?# "< b" st)
    (modify-syntax-entry ?\n "> b" st)
    st)
  "Syntax table for SwIPC mode")

(defconst swipc-re-interface-def "interface \\([a-zA-Z_][a-zA-Z0-9_:]*\\)")
(defconst swipc-re-interface-is-def "\\(is\\|, *\\) \\([a-zA-Z_][a-zA-Z0-9_:\\-]*\\)")
(defconst swipc-re-func-def "\\(\\[\\([0-9]+\\|0x[0-9a-fA-f]+\\)\\]\\) +\\([a-zA-Z_][a-zA-Z0-9_:]*\\)")
(defconst swipc-re-func-arg "\\([a-zA-Z_][a-zA-Z0-9_:]*\\)\\(<[a-zA-Z0-9_:, ]+>\\)?\\( \\([a-zA-Z_][a-zA-Z0-9_:]*\\)\\)?")
(defconst swipc-re-type-def "type \\([a-zA-Z_][a-zA-Z0-9_:]*\\) = ")

(defconst swipc-highlights
  (list
   (list swipc-re-types 0 'font-lock-type-face)
   (list swipc-re-keywords 0 'font-lock-keyword-face)
   (list swipc-re-constants 0 'font-lock-constant-face)
   (list swipc-re-func-def '(1 font-lock-constant-face) '(3 font-lock-function-name-face) (list swipc-re-func-arg ")" nil '(1 font-lock-type-face t) '(4 font-lock-variable-name-face t t)))
   (list swipc-re-interface-def '(1 font-lock-type-face) (list swipc-re-interface-is-def "{" nil '(2 font-lock-string-face)))
   (list swipc-re-type-def 1 'font-lock-type-face)
   )
  "Highlighting expressions for SwIPC mode")

(defvaralias 'swipc-indent-offset 'tab-width
  "Indentation offset for SwIPC mode")

(defun swipc-indent-line ()
  "Indent current line as SwIPC definition."
  (let ((indent-col 0))
    (save-excursion
      (beginning-of-line)
      (condition-case nil
          (while t
            (backward-up-list 1)
            (when (looking-at "[[{]")
              (setq indent-col (+ indent-col swipc-indent-offset))))
        (error nil)))
    (save-excursion
      (back-to-indentation)
      (when (and (looking-at "[]}]") (>= indent-col swipc-indent-offset))
        (setq indent-col (- indent-col swipc-indent-offset))))
    (save-excursion
     (indent-line-to indent-col))))

(defun swipc-mode ()
  "Major mode for editing SwIPC files"
  (interactive)
  (kill-all-local-variables)
  (set-syntax-table swipc-mode-syntax-table)
  (use-local-map swipc-mode-map)
  (set (make-local-variable 'font-lock-defaults) '(swipc-highlights))
  (set (make-local-variable 'indent-line-function) 'swipc-indent-line)
  (setq major-mode 'swipc-mode)
  (setq mode-name "SwIPC")
  (setq-default indent-tabs-mode t)
  (setq-default tab-width 4)
  (run-hooks 'swipc-mode-hook))

(provide 'swipc-mode)
