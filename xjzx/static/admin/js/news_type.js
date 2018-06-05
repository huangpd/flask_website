function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function(){
    var $a = $('.edit');
    var $add = $('.addtype');
    var $pop = $('.pop_con');
    var $cancel = $('.cancel');
    var $confirm = $('.confirm');
    var $error = $('.error_tip');
    var $input = $('.input_txt3');
    var sHandler = 'edit';
    var sId = 0;

    vue_list_con = new Vue({
        el:'.common_table',
        delimiters:['[[',']]'],
        data:{
            category_list:[]
        },
        methods:{
            add:function () {
                sHandler = 'add';
                $pop.find('h3').html('新增分类');
                $input.val('');
                $pop.show();
            },

            edit:function (event) {
                $this=$(event.target);
                sHandler = 'edit';
                sId = $this.parent().siblings().eq(0).html();
                $pop.find('h3').html('修改分类');
                $pop.find('.input_txt3').val($(this).parent().prev().html());
                $pop.show();
            },
            delete:function (event) {
                //
            }
        }
    });
    get_list();



    $cancel.click(function(){
        $pop.hide();
        $error.hide();
    });

    $input.click(function(){
        $error.hide();
    });


    $confirm.click(function(){
        if(sHandler=='edit') {
            var sVal = $input.val();
            if(sVal=='')
            {
                $error.html('输入框不能为空').show();
                return;
            }
            // 修改处理
            $.post('/admin/news_type_edit',{
                'csrf_token': $('#csrf_token').val(),
                'name': sVal,
                'id':sId
            },function (data) {
                if(data.result==1){
                    get_list();
                    $cancel.click();
                }else if(data.result==2){
                    $error.html('此名称已经存在').show();
                }
            });
        }
        else
        {
            var sVal = $input.val();
            if(sVal=='')
            {
                $error.html('输入框不能为空').show();
                return;
            }
            //添加处理
             $.post('/admin/news_type_add',{
                'csrf_token': $('#csrf_token').val(),
                'name': sVal,
            },function (data) {
                if(data.result==1){
                    get_list();
                    $cancel.click();
                }else if(data.result==2){
                    $error.html('此名称已经存在').show();
                }
            });

        }

    })
})

function get_list() {
    $.get('/admin/news_type_list', function (data) {
        vue_list_con.category_list = data.category_list;
    })
}