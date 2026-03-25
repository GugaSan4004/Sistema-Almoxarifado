{
    window.prepareExitValues = function () {
        const inpPeople = document.getElementById('inp_people');
        const inpDate = document.getElementById('inp_date');
        const subPeople = document.getElementById('sub_people');
        const subDate = document.getElementById('sub_date');

        if (inpPeople && subPeople) subPeople.value = inpPeople.value;
        if (inpDate && subDate) subDate.value = inpDate.value;
    }
}
