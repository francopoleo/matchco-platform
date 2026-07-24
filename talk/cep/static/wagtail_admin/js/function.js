$(document).ready(function () {
    const BUSINESS_UNIT_INPUT = $('.user-business-unit-class').find('select[id="id_business_unit"]');
    const FUNCTION_INPUT = $('.user-job-function-class').find('select[id="id_job_function"]');


    BUSINESS_UNIT_INPUT.on('change', async function (ev) {
        let data = []

        $(BUSINESS_UNIT_INPUT).children('option:checked').each((index, el) => {
            if($(el).val().length){
                data.push(parseInt($(el).val()))
            }
        })


        const response = await $.ajax({
            url: `${window.location.origin}/job-functions/users/api/`,
            data: {ids: data},
            traditional: true,
        });


        FUNCTION_INPUT.empty();

        FUNCTION_INPUT.append(`<option value="" disabled selected >--------</option>`)
        response.map((data) => {
            FUNCTION_INPUT.append(`<option value="${data.id}">${data.name}</option>`)
        });
    });
});
