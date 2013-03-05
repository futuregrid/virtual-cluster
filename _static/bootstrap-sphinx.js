var sphinx = window.sphinx || {};
sphinx['init'] = function($win, $nav, $subnav){
  /**
   * Get the absolute position of the supplied element within the document,
   * regardless of scroll offsets.
   */
  sphinx['absolutePosition'] = function (el) {
    var curleft = 0, curtop = 0;
    if (el.offsetParent) {
      do {
        curleft += el.offsetLeft;
        curtop += el.offsetTop;
      } while (el = el.offsetParent);
      return {left: curleft, top: curtop};
    }
    return {left: 0, top: 0};
  };
  /**
   * Initialize the sidebar to support fixed positioning.
   */
  sphinx['initSideNav'] = function(){
    var $sidebar = $('.page-sidebar');
    var $sidenav = $sidebar.find('> .well');
    $win.on('resize', function(){
      $sidenav.width($sidebar.width())
    }).resize();
    $sidenav.affix();
  };

  /**
   * Initialize top nav flyout menus to position the submenus more
   * intelligently to reduce the chance that they overflow off screen.
   */
  sphinx['initTopNav'] = function(){
    $('#navbar .nav li.dropdown-submenu').hover(
      function(){
        function menuTop($el){
          if ($el.is('.dropdown-menu')){
            var top = $el.offset().top;
            var bot = top + $el.height();
            if (bot > $win.height()){
              var $parent = $el.parent();
              var parenttop = menuTop($parent.parent());
              var botalign = -($el.height() - $parent.height());
              if ((top + botalign + parenttop) > 0){
                return botalign;
              }
              // the true top offset of the parent menu accounting for negative
              // css offset
              var menutop = $parent.closest('.dropdown-menu').offset().top + parenttop;
              return menutop - top - parenttop;
            }
          }
          return 0;
        }

        var $submenu = $(this).find('> ul');
        var subtop = menuTop($submenu);
        $submenu.css({
          position: 'absolute',
          top: subtop + 'px'
        });
      },
      function(){
        $(this).find('> ul').css('top', 0);
      }
    );
  };

  /**
   * Initialize handling of hash links, and loading of a page linking to a
   * hash, to account for fixed position header elements.
   */
  sphinx['initHashLinks'] = function(){
    $win.hashchange(function(){
      if (location.hash){
        var $target = $(location.hash.replace(/^#/, '#_'));
        if (/^_id\d+$/.test($target.attr('id')) && !$target.is('.section')){
          $target = $target.parent('[id]');
        }
        var padding = parseInt($target.css('padding-top').replace('px', ''), 10)
        var spacing = isNaN(padding) ? 0 : padding;
        var navOffset = spacing > 10 ? -(spacing - 5) : 5;
        var firstSection = '.content > .section';
        if ($target.is(firstSection) ||
           ($target.is('span') && $target.parent().is(firstSection)))
        {
          $win.scrollTop(0);
          // for android browsers
          $win.load(function(){$win.scrollTop(0);});
          return;
        }

        if ($nav.css('position') == 'fixed'){
          navOffset += $nav.outerHeight();
        }

        $win.scrollTop(sphinx.absolutePosition($target.get(0)).top - navOffset);
        var $animate = $target;
        if ($animate.is('.section')){
          $animate = $animate.find('> h2');
        } else if ($animate.is('ul')){
          $animate = $animate.find('li:first-child :first-child');
        }
        $animate.animate({opacity: 0.4}, 1000, function(){
          $animate.animate({opacity: 1}, 1000);
        });
      }
    }).hashchange();
  };

  sphinx['initScrollspy'] = function(){
    var navOffset = 10;
    navOffset += $nav.outerHeight();

    // wait on all other events
    setTimeout(function(){
      $('body').scrollspy({offset: navOffset, target: '.page-toc'});
      $win.on('load resize', function(){
        $('body').scrollspy('refresh');
      });
      $win.on('scroll', function(){
        if($win.scrollTop() == 0){
          $('body').data('scrollspy').activeTarget = null;
          $('.page-toc').find('li.active').removeClass('active');
        }
      });
    }, 0);
  };

  // Enable dropdown.
  $('.dropdown-toggle').dropdown();

  // fix the navbar to the top w/ js so that if the js doesn't load, hash links
  // aren't screwed (must be before initHashLinks).
  $nav.addClass('navbar-fixed-top').removeClass('no-js');
  $('body').addClass('with-fixed-nav');

  // alter element ids so we can handle hash links ourselves accounting for
  // fixed positioned nav elements.
  $('.content *[id]').each(function(index, el){
    var $el = $(el);
    $el.attr('id', '_' + $el.attr('id'));
  });
  // update nav links accordingly for scrollspy
  $('.nav *[href^=#]').each(function(index, el){
    var $el = $(el);
    $el.attr('data-target', '#_' + $el.attr('href').replace('#', ''));
    $el.click(function(){
      // force a hashchange if the hash is already set to the href
      if (location.hash == $(this).attr('href')){
        $win.hashchange();
      }
    });
  });

  sphinx.initTopNav();
  sphinx.initSideNav();

  sphinx.initHashLinks();
  sphinx.initScrollspy();
};

$(document).ready(function() {
  sphinx.init($(window), $('#navbar'), $('.subnav'));
});