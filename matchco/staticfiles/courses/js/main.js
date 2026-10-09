$(document).ready(function () {
    $('#subject-select-input').on('change', function (ev) {
        window.location.replace(this.value);
    })
});