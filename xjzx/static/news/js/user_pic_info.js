function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $('.pic_info').submit(function (e) {
        // 禁止浏览器对于表单的默认行为
        e.preventDefault();

        $(this).ajaxSubmit({
            url: "/user/pic",
            type: "post",
            dataType: "json",
            success:function (data) {
                alert(122345);
                if (data.result == 1) {
                   //　修改user.html中头像图片
                    alert("hahahahahaha");
                    $('.now_user_pic').attr('src', data.avatar_url);
                    $('.user_center_pic>img', parent.document).attr('src',data.avatar_url);
                    $('.lgin_pic', parent.document).attr('src',data.avatar_url);
                }
            }
        });
    });
})