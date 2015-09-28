#! /usr/bin/perl

use warnings;
use strict;
use utf8;

use CGI qw/:standard/;
use CGI::Carp qw/fatalsToBrowser/;
use GD;
use POSIX qw/floor/;
use Encode;

use constant PI    => 4 * atan2(1, 1);

my ($WIDTH, $HEIGHT) = (180, 62);

my $url = url();

my @alphabet = split('', '0123456789абвгдеёжзийклмнопрстуфхцчшщъыьэюя');
#my @alphabet = split('', '0123456789abcdefghijklmnopqrstuvwxyz');

my $mode = param('mode') || 'form';
my $str  = decode('utf-8', param('s')) || random_str();
my $seed = param('r') || time + $$;

my @fonts = qw(
    /home/kappa/work/rcaptcha/untone2.png
);
#/home/kappa/work/rcaptcha/rockwell.png
#/home/kappa/work/rcaptcha/baskerville.png

srand($seed);

$| = 0;

if    ($mode eq 'form')     { print_form(); }
elsif ($mode eq 'image')    { print_image(); }
else                        { print header, "Unknown mode" }

exit;

sub print_form {
    srand(time + $$);
    my $new_seed = int rand 99999;
    my $new_str = random_str();

    print header(-charset => 'utf-8'),
        qq{<img src="$url?mode=image;s=$str;r=$seed" width="@{[$WIDTH*4]}" height="@{[$HEIGHT*4]}"><br>},
        qq{<a href="$url?s=$str;r=$new_seed">refresh effects</a><br>},
        qq{<a href="$url?s=$new_str;r=$seed">refresh string</a><br>},
        qq{<a href="$url?s=$str">random effects</a><br>},
        qq{<a href="$url">random all</a><br>};
}

sub print_image {
    my $im = GD::Image->newTrueColor($WIDTH, $HEIGHT);

    my $real_w = image_draw_text($im, $str);
    image_filter_lines($im, $real_w, length($str));
    $im = image_filter_wave($im, $WIDTH / 2);

    print "Content-type: image/png\n\n";

    binmode STDOUT;
    print $im->png;
}

sub image_draw_text {
    my ($im, $text) = @_;

    # store image dimensions for convinient use

    my $w = $im->width;
    my $h = $im->height;

    # some initial drawing

    my $white = $im->colorAllocate(255, 255, 255);
    my $black = $im->colorAllocate(0, 0, 0);
    $im->filledRectangle(0, 0, $im->width - 1, $im->height - 1, $white);

    my $font_file = $fonts[int(rand(@fonts))];
    my $font = GD::Image->newFromPng($font_file, 1) or die "Cannot load font $font_file";

    my $fontfile_width = $font->width;
    my $fontfile_height = $font->height -1;
    my %font_metrics;
    my $symbol = 0;
    my $reading_symbol = 0;

    # loading font
    my $i;
    for ($i = 0; $i < $fontfile_width && $symbol < @alphabet; $i++) {
        my ($r,$g,$b) =  $font->rgb($font->getPixel($i, 0));
        my $transparent = 1;
        if ($r == 0 && $g == 0 && $b == 0) {
            $transparent = 0;
        }

        if(!$reading_symbol && !$transparent) {
            $font_metrics{$alphabet[$symbol]}->{'start'} = $i;
            $reading_symbol = 1;
            next;
        }

        if($reading_symbol && $transparent) {
            $font_metrics{$alphabet[$symbol]}->{'end'} = $i;
            $reading_symbol = 0;
            $symbol ++;
            next;
        }
    }
    $font_metrics{$alphabet[$symbol]}->{'end'} = $i - 1;    # close last symbol

    # draw text
    my $x = 10;
    foreach my $c (split '', $text) {
        my $m = $font_metrics{$c};

        my $y = int(rand(5)) - 5  + ($h - $fontfile_height)/2 + 2;

        $im->copy($font, $x-1, $y, $m->{'start'}, 1, $m->{'end'} - $m->{'start'}, $fontfile_height);
        $x += $m->{'end'} - $m->{'start'} - 1;
    }

    # apply distortion filters
    # return results

    return $x;
}

sub image_filter_wave {
    my $im = shift;
    my $center = shift;

    my $im2 = GD::Image->newTrueColor($WIDTH, $HEIGHT);
    $im2->alphaBlending(1);
    $im2->filledRectangle(0, 0, $im2->width - 1, $im2->height - 1, $im2->colorAllocate(255, 255, 255));

    my $w = $im->width();
    my $h = $im->height();

    # coefficients

    my $rand1 = (rand(450000) + 750000) / 10000000;
    my $rand2 = (rand(450000) + 750000) / 10000000;
    my $rand3 = (rand(450000) + 750000) / 10000000;
    my $rand4 = (rand(450000) + 750000) / 10000000;

    # phases

    my $rand5 = rand(PI);
    my $rand6 = rand(PI);
    my $rand7 = rand(PI);
    my $rand8 = rand(PI);

    # amplitudes
    my $rand9 = (rand(90) + 330) / 90;
    my $rand10 = (rand(120) + 330) / 220;

    for (my $x = 0; $x < $w; $x++) {
        for (my $y = 0; $y < $h; $y++) {
            my $sx = $x + (sin($x * $rand1 + $rand5) + sin($y * $rand3 + $rand6)) * $rand9 - $w / 2 + $center + 1;
            my $sy = $y + (sin($x * $rand2 + $rand7) + sin($y * $rand4 + $rand8)) * $rand10;

            my $color;
            my $color_x;
            my $color_y;
            my $color_xy;
            my $newcolor;

            if($sx < 0 || $sy < 0 || $sx >= $w - 1 || $sy >= $h - 1) {
                next;
            } else {
                $color = $im->getPixel($sx, $sy) & 0xFF;
                $color_x = $im->getPixel($sx + 1, $sy) & 0xFF;
                $color_y = $im->getPixel($sx, $sy + 1) & 0xFF;
                $color_xy = $im->getPixel($sx + 1, $sy + 1) & 0xFF;
            }

            if($color==255 && $color_x==255 && $color_y==255 && $color_xy==255) {
                next;
            } else {
                my $frsx = $sx - POSIX::floor($sx);
                my $frsy = $sy - POSIX::floor($sy);
                my $frsx1 = 1 - $frsx;
                my $frsy1 = 1 - $frsy;

                $newcolor=(
                    $color * $frsx1 * $frsy1 +
                    $color_x * $frsx * $frsy1 +
                    $color_y * $frsx1 * $frsy +
                    $color_xy * $frsx * $frsy);

                if($newcolor > 255) {
                    $newcolor = 255;
                }

                $newcolor = $newcolor;

                $im2->setPixel($x, $y, $im2->colorAllocate($newcolor, $newcolor, $newcolor));
            }
        }
    }

    return $im2;
}

sub image_filter_lines {
    my ($im, $w, $n) = @_;

    my $h = $im->height();

    my $black = $im->colorAllocate(0, 0, 0);
    my $white = $im->colorAllocate(255, 255, 255);

    my ($x1, $x2, $y1, $y2) = (-rand($w / $n), 0, 0, 0);
    foreach (0 .. $n * 2) {
        $x1 += $w / ($n * 2);
        $x2 = $x1 + rand($w / $n / 2) - $w / $n;
        $y1 = rand($h / 3);
        $y2 = $y2 + rand($h);

        $im->setThickness(2);

        $im->line($x1, $y1, $x2, $y2, $white);
    }

    foreach (0 .. int(rand(3))) {
        my $x1 = rand($w / 3);
        my $x2 = rand($w / 2) + $w / 2;
        my $y1 = rand($h);
        my $y2 = rand($h);

        $im->setThickness(2);

        $im->line($x1, $y1, $x2, $y2, $black);
    }
}

sub random_str {
    return join '', map { $alphabet[rand scalar @alphabet] } 0 .. rand(3) + 4;
}
