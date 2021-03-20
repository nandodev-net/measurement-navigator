$(".mobile-menu").on('click', function() {
    var $this = $(this);
    $this.toggleClass('on');
});
$("#mobile-collapse").on('click', function() {
    if (vw > 991) {
        $(".pcoded-navbar:not(.theme-horizontal)").toggleClass("navbar-collapsed");
    }
});
$(".mob-toggler").on('click', function() {
    $('.pcoded-header > .collapse,.pcoded-header > .container > .collapse').toggleClass('d-flex');
});

$("#mobile-collapse,#mobile-collapse1").click(function(e) {
    var vw = $(window)[0].innerWidth;
    if (vw < 992) {
        $(".pcoded-navbar").toggleClass('mob-open');
        e.stopPropagation();
    }
});

var vw = $(window)[0].innerWidth;
$(".pcoded-navbar").on('click tap', function(e) {
    e.stopPropagation();
});
$('.pcoded-main-container,.pcoded-header').on("click", function() {
    if (vw < 992) {
        if ($(".pcoded-navbar").hasClass("mob-open") == true) {
            $(".pcoded-navbar").removeClass('mob-open');
            $("#mobile-collapse,#mobile-collapse1").removeClass('on');
        }
    }
});


// =============   layout builder   =============
$.fn.pcodedmenu = function(settings) {
    var oid = this.attr("id");
    var defaults = {
        themelayout: 'vertical',
        MenuTrigger: 'click',
        SubMenuTrigger: 'click',
    };
    var settings = $.extend({}, defaults, settings);
    var PcodedMenu = {
        PcodedMenuInit: function() {
            PcodedMenu.HandleMenuTrigger();
            PcodedMenu.HandleSubMenuTrigger();
            PcodedMenu.HandleOffset();
        },
        HandleSubMenuTrigger: function() {
            var $window = $(window);
            var newSize = $window.width();
            if ($('.pcoded-navbar').hasClass('theme-horizontal') == true || $('.pcoded-navbar').hasClass('theme-horizontal-dis') == true) {
                if ((newSize >= 992 && $('body').hasClass('layout-6') || (newSize >= 992 && $('body').hasClass('layout-7')))) {
                    var $dropdown = $("body[class*='layout-6'] .theme-horizontal .pcoded-inner-navbar .pcoded-submenu > li.pcoded-hasmenu, body[class*='layout-7'] .theme-horizontal .pcoded-inner-navbar .pcoded-submenu > li.pcoded-hasmenu");
                    $dropdown.off('click').off('mouseenter mouseleave').hover(
                        function() {
                            $(this).addClass('pcoded-trigger').addClass('active');
                        },
                        function() {
                            $(this).removeClass('pcoded-trigger').removeClass('active');
                        }
                    );
                } else {
                    if ($('body').hasClass('layout-6') || $('body').hasClass('layout-7')) {
                        if ($('.pcoded-navbar').hasClass('theme-horizontal-dis')) {
                            var $dropdown = $(".pcoded-navbar.theme-horizontal-dis .pcoded-inner-navbar .pcoded-submenu > li.pcoded-hasmenu");
                            $dropdown.off('click').off('mouseenter mouseleave').hover(
                                function() {
                                    $(this).addClass('pcoded-trigger').addClass('active');
                                },
                                function() {
                                    $(this).removeClass('pcoded-trigger').removeClass('active');
                                }
                            );
                        }
                        if (!$('.pcoded-navbar').hasClass('theme-horizontal-dis')) {
                            var $dropdown = $(".pcoded-navbar:not(.theme-horizontal-dis) .pcoded-inner-navbar .pcoded-submenu > li > .pcoded-submenu > li");
                            $dropdown.off('mouseenter mouseleave').off('click').on('click',
                                function() {
                                    var str = $(this).closest('.pcoded-submenu').length;
                                    if (str === 0) {
                                        if ($(this).hasClass('pcoded-trigger')) {
                                            $(this).removeClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideUp();
                                        } else {
                                            $('.pcoded-submenu > li > .pcoded-submenu > li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                            $(this).closest('.pcoded-inner-navbar').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                            $(this).addClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideDown();
                                        }
                                    } else {
                                        if ($(this).hasClass('pcoded-trigger')) {
                                            $(this).removeClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideUp();
                                        } else {
                                            $('.pcoded-submenu > li > .pcoded-submenu > li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                            $(this).closest('.pcoded-submenu').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                            $(this).addClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideDown();
                                        }
                                    }
                                });
                            $(".pcoded-inner-navbar .pcoded-submenu > li > .pcoded-submenu > li").on('click', function(e) {
                                e.stopPropagation();
                                var str = $(this).closest('.pcoded-submenu').length;
                                if (str === 0) {
                                    if ($(this).hasClass('pcoded-trigger')) {
                                        $(this).removeClass('pcoded-trigger');
                                        $(this).children('.pcoded-submenu').slideUp();
                                    } else {
                                        $('.pcoded-hasmenu li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                        $(this).closest('.pcoded-inner-navbar').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                        $(this).addClass('pcoded-trigger');
                                        $(this).children('.pcoded-submenu').slideDown();
                                    }
                                } else {
                                    if ($(this).hasClass('pcoded-trigger')) {
                                        $(this).removeClass('pcoded-trigger');
                                        $(this).children('.pcoded-submenu').slideUp();
                                    } else {
                                        $('.pcoded-hasmenu li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                        $(this).closest('.pcoded-submenu').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                        $(this).addClass('pcoded-trigger');
                                        $(this).children('.pcoded-submenu').slideDown();
                                    }
                                }
                            });
                        }
                    } else {
                        if (newSize >= 992) {
                            var $dropdown = $(".pcoded-navbar.theme-horizontal .pcoded-inner-navbar .pcoded-submenu > li.pcoded-hasmenu");
                            $dropdown.off('click').off('mouseenter mouseleave').hover(
                                function() {
                                    $(this).addClass('pcoded-trigger').addClass('active');
                                },
                                function() {
                                    $(this).removeClass('pcoded-trigger').removeClass('active');
                                }
                            );
                        } else {
                            var $dropdown = $(".pcoded-navbar.theme-horizontal-dis .pcoded-inner-navbar .pcoded-submenu > li > .pcoded-submenu > li");
                            $dropdown.off('mouseenter mouseleave').off('click').on('click',
                                function() {
                                    var str = $(this).closest('.pcoded-submenu').length;
                                    if (str === 0) {
                                        if ($(this).hasClass('pcoded-trigger')) {
                                            $(this).removeClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideUp();
                                        } else {
                                            $('.pcoded-submenu > li > .pcoded-submenu > li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                            $(this).closest('.pcoded-inner-navbar').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                            $(this).addClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideDown();
                                        }
                                    } else {
                                        if ($(this).hasClass('pcoded-trigger')) {
                                            $(this).removeClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideUp();
                                        } else {
                                            $('.pcoded-submenu > li > .pcoded-submenu > li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                            $(this).closest('.pcoded-submenu').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                            $(this).addClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideDown();
                                        }
                                    }
                                });
                        }
                    }
                }
            }
            switch (settings.SubMenuTrigger) {
                case 'click':
                    $('.pcoded-navbar .pcoded-hasmenu').removeClass('is-hover');
                    $(".pcoded-inner-navbar .pcoded-submenu > li > .pcoded-submenu > li").on('click', function(e) {
                        e.stopPropagation();
                        var str = $(this).closest('.pcoded-submenu').length;
                        if (str === 0) {
                            if ($(this).hasClass('pcoded-trigger')) {
                                $(this).removeClass('pcoded-trigger');
                                $(this).children('.pcoded-submenu').slideUp();
                            } else {
                                $('.pcoded-submenu > li > .pcoded-submenu > li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                $(this).closest('.pcoded-inner-navbar').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                $(this).addClass('pcoded-trigger');
                                $(this).children('.pcoded-submenu').slideDown();
                            }
                        } else {
                            if ($(this).hasClass('pcoded-trigger')) {
                                $(this).removeClass('pcoded-trigger');
                                $(this).children('.pcoded-submenu').slideUp();
                            } else {
                                $('.pcoded-submenu > li > .pcoded-submenu > li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                $(this).closest('.pcoded-submenu').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                $(this).addClass('pcoded-trigger');
                                $(this).children('.pcoded-submenu').slideDown();
                            }
                        }
                    });
                    $(".pcoded-submenu > li").on('click', function(e) {
                        e.stopPropagation();
                        var str = $(this).closest('.pcoded-submenu').length;
                        if (str === 0) {
                            if ($(this).hasClass('pcoded-trigger')) {
                                $(this).removeClass('pcoded-trigger');
                                $(this).children('.pcoded-submenu').slideUp();
                            } else {
                                $('.pcoded-hasmenu li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                $(this).closest('.pcoded-inner-navbar').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                $(this).addClass('pcoded-trigger');
                                $(this).children('.pcoded-submenu').slideDown();
                            }
                        } else {
                            if ($(this).hasClass('pcoded-trigger')) {
                                $(this).removeClass('pcoded-trigger');
                                $(this).children('.pcoded-submenu').slideUp();
                            } else {
                                $('.pcoded-hasmenu li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                $(this).closest('.pcoded-submenu').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                $(this).addClass('pcoded-trigger');
                                $(this).children('.pcoded-submenu').slideDown();
                            }
                        }
                    });
                    break;
            }
        },
        HandleMenuTrigger: function() {
            var $window = $(window);
            var newSize = $window.width();
            if (newSize >= 992) {
                if ($('.pcoded-navbar').hasClass('theme-horizontal') == true) {
                    if ((newSize >= 768 && $('body').hasClass('layout-6') || (newSize >= 768 && $('body').hasClass('layout-7')))) {
                        var $dropdown = $("body[class*='layout-6'] .theme-horizontal .pcoded-inner-navbar > li,body[class*='layout-7'] .theme-horizontal .pcoded-inner-navbar > li ");
                        $dropdown.off('click').off('mouseenter mouseleave').hover(
                            function() {
                                $(this).addClass('pcoded-trigger').addClass('active');
                                if ($('.pcoded-submenu', this).length) {
                                    var elm = $('.pcoded-submenu:first', this);
                                    var off = elm.offset();
                                    var l = off.left;
                                    var w = elm.width();
                                    var docH = $(window).height();
                                    var docW = $(window).width();

                                    var isEntirelyVisible = (l + w <= docW);
                                    if (!isEntirelyVisible) {
                                        var temp = $('.sidenav-inner').attr('style');
                                        $('.sidenav-inner').css({
                                            'margin-left': (parseInt(temp.slice(12, temp.length - 3)) - 80)
                                        });
                                        $('.sidenav-horizontal-prev').removeClass('disabled');
                                    } else {
                                        $(this).removeClass('edge');
                                    }
                                }
                            },
                            function() {
                                $(this).removeClass('pcoded-trigger').removeClass('active');
                            }
                        );
                    } else {
                        if ($('body').hasClass('layout-6') || $('body').hasClass('layout-7')) {
                            if ($('.pcoded-navbar').hasClass('theme-horizontal-dis')) {
                                var $dropdown = $(".pcoded-navbar.theme-horizontal-dis .pcoded-inner-navbar > li");
                                $dropdown.off('click').off('mouseenter mouseleave').hover(
                                    function() {
                                        $(this).addClass('pcoded-trigger').addClass('active');
                                        if ($('.pcoded-submenu', this).length) {
                                            var elm = $('.pcoded-submenu:first', this);
                                            var off = elm.offset();
                                            var l = off.left;
                                            var w = elm.width();
                                            var docH = $(window).height();
                                            var docW = $(window).width();

                                            var isEntirelyVisible = (l + w <= docW);
                                            if (!isEntirelyVisible) {
                                                var temp = $('.sidenav-inner').attr('style');
                                                $('.sidenav-inner').css({
                                                    'margin-left': (parseInt(temp.slice(12, temp.length - 3)) - 80)
                                                });
                                                $('.sidenav-horizontal-prev').removeClass('disabled');
                                            } else {
                                                $(this).removeClass('edge');
                                            }
                                        }
                                    },
                                    function() {
                                        $(this).removeClass('pcoded-trigger').removeClass('active');
                                    }
                                );
                            }
                            if (!$('.pcoded-navbar').hasClass('theme-horizontal-dis')) {
                                var $dropdown = $(".pcoded-navbar:not(.theme-horizontal-dis) .pcoded-inner-navbar > li");
                                $dropdown.off('mouseenter mouseleave').off('click').on('click',
                                    function() {
                                        if ($(this).hasClass('pcoded-trigger')) {
                                            $(this).removeClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideUp();
                                        } else {
                                            $('li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                                            $(this).closest('.pcoded-inner-navbar').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                                            $(this).addClass('pcoded-trigger');
                                            $(this).children('.pcoded-submenu').slideDown();
                                        }
                                    }
                                );
                            }
                        } else {
                            var $dropdown = $(".theme-horizontal .pcoded-inner-navbar > li");
                            $dropdown.off('click').off('mouseenter mouseleave').hover(
                                function() {
                                    $(this).addClass('pcoded-trigger').addClass('active');
                                    if ($('.pcoded-submenu', this).length) {
                                        var elm = $('.pcoded-submenu:first', this);
                                        var off = elm.offset();
                                        var l = off.left;
                                        var w = elm.width();
                                        var docH = $(window).height();
                                        var docW = $(window).width();

                                        var isEntirelyVisible = (l + w <= docW);
                                        if (!isEntirelyVisible) {
                                            var temp = $('.sidenav-inner').attr('style');
                                            $('.sidenav-inner').css({
                                                'margin-left': (parseInt(temp.slice(12, temp.length - 3)) - 80)
                                            });
                                            $('.sidenav-horizontal-prev').removeClass('disabled');
                                        } else {
                                            $(this).removeClass('edge');
                                        }
                                    }
                                },
                                function() {
                                    $(this).removeClass('pcoded-trigger').removeClass('active');
                                }
                            );
                        }
                    }
                }
            } else {
                var $dropdown = $(".pcoded-navbar.theme-horizontal-dis .pcoded-inner-navbar > li");
                $dropdown.off('mouseenter mouseleave').off('click').on('click',
                    function() {
                        if ($(this).hasClass('pcoded-trigger')) {
                            $(this).removeClass('pcoded-trigger');
                            $(this).children('.pcoded-submenu').slideUp();
                        } else {
                            $('li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                            $(this).closest('.pcoded-inner-navbar').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                            $(this).addClass('pcoded-trigger');
                            $(this).children('.pcoded-submenu').slideDown();
                        }
                    });
            }
            switch (settings.MenuTrigger) {
                case 'click':
                    $('.pcoded-navbar').removeClass('is-hover');
                    $(".pcoded-inner-navbar > li:not(.pcoded-menu-caption) ").on('click', function() {
                        if ($(this).hasClass('pcoded-trigger')) {
                            $(this).removeClass('pcoded-trigger');
                            $(this).children('.pcoded-submenu').slideUp();
                        } else {
                            $('li.pcoded-trigger').children('.pcoded-submenu').slideUp();
                            $(this).closest('.pcoded-inner-navbar').find('li.pcoded-trigger').removeClass('pcoded-trigger');
                            $(this).addClass('pcoded-trigger');
                            $(this).children('.pcoded-submenu').slideDown();
                        }
                    });
                    break;
            }
        },
        HandleOffset: function() {
            switch (settings.themelayout) {
                case 'horizontal':
                    var trigger = settings.SubMenuTrigger;
                    if (trigger === "hover") {
                        $("li.pcoded-hasmenu").on('mouseenter mouseleave', function(e) {
                            if ($('.pcoded-submenu', this).length) {
                                var elm = $('.pcoded-submenu:first', this);
                                var off = elm.offset();
                                var l = off.left;
                                var w = elm.width();
                                var docH = $(window).height();
                                var docW = $(window).width();

                                var isEntirelyVisible = (l + w <= docW);
                                if (!isEntirelyVisible) {
                                    $(this).addClass('edge');
                                } else {
                                    $(this).removeClass('edge');
                                }
                            }
                        });
                    } else {
                        $("li.pcoded-hasmenu").on('click', function(e) {
                            e.preventDefault();
                            if ($('.pcoded-submenu', this).length) {
                                var elm = $('.pcoded-submenu:first', this);
                                var off = elm.offset();
                                var l = off.left;
                                var w = elm.width();
                                var docH = $(window).height();
                                var docW = $(window).width();

                                var isEntirelyVisible = (l + w <= docW);
                                if (!isEntirelyVisible) {
                                    $(this).toggleClass('edge');
                                }
                            }
                        });
                    }
                    break;
                default:
            }
        },
    };
    PcodedMenu.PcodedMenuInit();
};
$("#pcoded").pcodedmenu({
    MenuTrigger: 'click',
    SubMenuTrigger: 'click',
});