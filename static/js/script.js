document.addEventListener("DOMContentLoaded", function () {
    const interviewForm = document.getElementById("interviewForm");
    const answerArea = document.getElementById("answerArea");
    const submitBtn = document.getElementById("submitBtn");

    if (interviewForm && answerArea) {
        // Submit via Ctrl/Cmd + Enter
        answerArea.addEventListener("keydown", function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                e.preventDefault();
                submitForm();
            }
        });

        // Form submission event handler
        interviewForm.addEventListener("submit", function (e) {
            e.preventDefault();
            submitForm();
        });

        function submitForm() {
            const answerText = answerArea.value.trim();
            if (!answerText) {
                if (!confirm("Your answer box is empty. Do you want to submit a blank response?")) {
                    return;
                }
            }

            // Disable submit button and toggle loading state to prevent duplicate clicks
            if (submitBtn) {
                submitBtn.disabled = true;
                const btnText = submitBtn.querySelector(".btn-text");
                const spinner = submitBtn.querySelector(".spinner");
                if (btnText) btnText.innerText = "Evaluating Answer...";
                if (spinner) spinner.style.display = "inline-block";
            }

            interviewForm.submit();
        }

        // Warn before accidental page reload/leave during interview
        window.addEventListener("beforeunload", function (e) {
            if (answerArea.value.trim().length > 0 && !submitBtn.disabled) {
                e.preventDefault();
                e.returnValue = "";
            }
        });
    }
});