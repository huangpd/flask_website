// 解析url中的查询字符串
function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

// news_collect
$(function(){
    // 关注当前用户
    $(".focus").click(function () {
        $.post('/userfollow',{
            'csrf_token':$('#csrf_token').val(),
            'action':1,
            'follow_user_id':$('#user_id').val()
        },function (data) {
            if(data.result==1){
                $('.login_btn').click();
            }
            else if(data.result==2){
                $('.focus').hide();
                $('.focused').show();
            }
        })
    })

    // 取消关注
    $(".focused").click(function () {
        $.post('/userfollow',{
            'csrf_token':$('#csrf_token').val(),
            'action':2,
            'follow_user_id':$('#user_id').val()
        },function (data) {
            if(data.result==1){
                $('.login_btn').click();
            }
            else if(data.result==2){
                $('.focus').show();
                $('.focused').hide();
            }
        })
    })
})
