$(document).ready(function() {
    // Header scroll effect
    $(window).on('scroll', function() {
        if ($(this).scrollTop() > 50) {
            $('#header').addClass('scrolled');
        } else {
            $('#header').removeClass('scrolled');
        }
    });

    // Mobile menu toggle
    $('#hamburger').on('click', function() {
        $(this).toggleClass('active');
        $('#mobileMenu').toggleClass('active');
        $('body').toggleClass('menu-open');
    });

    // Close mobile menu on link click
    $('.mobile-nav-link').on('click', function() {
        $('#hamburger').removeClass('active');
        $('#mobileMenu').removeClass('active');
        $('body').removeClass('menu-open');
    });

    // Smooth scroll for anchor links
    $('a[href^="#"]').on('click', function(e) {
        var target = $(this.getAttribute('href'));
        if (target.length) {
            e.preventDefault();
            $('html, body').animate({
                scrollTop: target.offset().top - 72
            }, 600);
        }
    });

    // Card hover effects with jQuery
    $('.card').on('mouseenter', function() {
        $(this).find('.card-overlay').css('background', 'linear-gradient(180deg, rgba(5, 8, 11, 0.2) 0%, rgba(5, 8, 11, 0.9) 100%)');
    }).on('mouseleave', function() {
        $(this).find('.card-overlay').css('background', 'linear-gradient(180deg, rgba(5, 8, 11, 0.3) 0%, rgba(5, 8, 11, 0.85) 100%)');
    });
});
