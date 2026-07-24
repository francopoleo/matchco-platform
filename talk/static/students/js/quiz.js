const urlContent = window.location.href;

const btnSubmitQuiz = $('#btn-submit-quiz');
const quizForm = $('#quiz-form');
const csrf = $("[name='csrfmiddlewaretoken']");
const elements = [...$('.ans')];

btnSubmitQuiz.on('click', e => {
    e.preventDefault();
    console.log(`${urlContent}save`)
    quizForm.submit();
})

const sendData = () => {
    const data = {};
    data['csrfmiddlewaretoken'] = csrf[0].value;

    elements.forEach(el => {
        if (el.checked) {
            data[el.name] = el.id;
        }
    })
    

    $.ajax({
        type: 'POST',
        url: `${urlContent}save/`,
        data: data,
        mode: 'same-origin',
        success: function (response) {
            console.log(response);
            return location.reload();
        },
        error: function (error) {
            console.log(error);
        }
    })

}

quizForm.on('submit', e => {
    e.preventDefault();

    sendData();
})