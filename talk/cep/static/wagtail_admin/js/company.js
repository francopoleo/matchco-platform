$(document).ready(function () {
    const COMPANY_INPUT = $('.company-class').find('select[id="id_company"]');
    const CHANNEL_INPUT = $('.company-channel-class').find('select[id="id_channels"]');

    function clearChildren() {
        CHANNEL_INPUT.empty();
    }

    COMPANY_INPUT.on('change', async function (ev) {
        clearChildren();
        let data = []

        $(COMPANY_INPUT).children('option:checked').each((index, el) => {
            if($(el).val().length){
                data.push(parseInt($(el).val()))
            }
        })

        const response = await $.ajax({
            url: `${window.location.origin}/business-channels/api/`,
            data: {ids: data},
            traditional: true,
        });

        let inputSelectToChange = CHANNEL_INPUT
        inputSelectToChange.empty();

        response.map((data) => {
            inputSelectToChange.append(`<option value="${data.id}">${data.name}</option>`)
        });
    });
});
